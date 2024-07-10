#include <linux/init.h>
#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/fs.h>
#include <linux/slab.h>
#include <linux/delay.h>
#include <linux/uaccess.h>
#include <linux/time.h>
#include <linux/of.h>
#include <linux/sched.h>

#include "../../../drivers/vendor/hisi/ap/platform/hi6250/global_ddr_map.h"
#include "../tzdriver/teek_ns_client.h"
#include "smc_forwarder.h"

// lock for smc ring buffer
static DEFINE_SPINLOCK(write_out_lock);
// lock for smc status value
static DEFINE_SPINLOCK(smc_status_lock);

// if 0: no smc will get executed, if > 0: execute smc and subtract, if < 0 just execute smc normally
int smc_exec_status = -1;

// if 0: no forwarding, if != 0: foward SMCs
int smc_forward = 0;

// shared mem of agents
void *agent_shared_mem_virt[5];
int agent_count = 0;

// number of SMCs the ring buffer can hold
#define SMC_CMD_MAX_SIZE    256
// SMC cmd ring buffer
TC_NS_SMC_CMD smc_out_ring[SMC_CMD_MAX_SIZE] = {{0}};
// SMC data ring buffer
struct smc_cmd_data smc_out_data_ring[SMC_CMD_MAX_SIZE] = {{0}};
// position values for read/write to ring buffers
unsigned int smc_out_pos_write = 0;
unsigned int smc_out_pos_read = 0;

// this has to be big enough to hold all of one smc data
#define OUT_BUFFER_SIZE 16777216
// allocate space for format string to copy to userland
char out_buffer[OUT_BUFFER_SIZE] = {0};


// easy way to access paramtype of i-th parameter
#define TEEC_PARAM_TYPE_GET( paramTypes, index) \
    (((paramTypes) >> (4*(index))) & 0x0F)
// used for allocation to round up to page size
#define ROUND_UP(N, S) ((((N) + (S) - 1) / (S)) * (S))

unsigned long virt_addr = 0;	

void set_agent_buffer_addr(void *buffer_addr)    {
    agent_shared_mem_virt[agent_count] = buffer_addr;
    agent_count += 1;
    printk("\nSHMAGENT set %x", buffer_addr);
}

TC_NS_SMC_CMD *smc_read_in()  {
    unsigned long t = 0;
    unsigned long flags;
    // lock 'smc__exec_status' for reading
    spin_lock_irqsave(&smc_status_lock, flags);
    // if 'smc_exec_status' is active not SMCs shoud get executed
    while(smc_exec_status >= 0)    {
        // release lock so 'smc_exec_status' can be changed
        spin_unlock_irqrestore(&smc_status_lock, flags);
        t = msleep_interruptible(50);
        if(t != 0)  {
            return 0;
        }
        // lock again
        spin_lock_irqsave(&smc_status_lock, flags);
        if(smc_exec_status > 0) {
            // if its greater than 0 execute smc and subtract
            smc_exec_status -= 1;
            printk("\nSMC_EXEC_STATUS added -> now %d", smc_exec_status);
            break;

        }
    }
    // if 'smc_exec_status' is not active just release lock again
    spin_unlock_irqrestore(&smc_status_lock, flags);
    return 0;
}

/*
    Use this function at any point in tzdriver if you want to save/forward the smc cmd into the ring buffer
    @param the smc cmd struct to be saved
    Also allocates space for every smc data like TC_Operation parameter on the heap 
    We NEED to read out and save the smc data here, later it will be gone
*/
int smc_write_out(TC_NS_SMC_CMD *smc_cmd, bool ret) {
    
    if(smc_forward == 0)    {
        //only used for timing
        printk("\nSMC_TIMESTAMP start of write_out of uid %x with event_nr %d\n", smc_cmd->uid, smc_cmd->event_nr);
        //printk("\nSMC_TIMESTAMP NOT forwarding of uid %x with event_nr %d\n", smc_cmd->uid, smc_cmd->event_nr);
        return 0;
    }
    //only used for timing
    printk("\nSMC_TIMESTAMP start of write_out of uid %x with event_nr %d\n", smc_cmd->uid, smc_cmd->event_nr);

    unsigned long flags;
    // lock access to ring buffers so no other process will write to it
    spin_lock_irqsave(&write_out_lock, flags);
    // copy smc cmd into ring buffer
    memcpy(&smc_out_ring[smc_out_pos_write], smc_cmd, sizeof(TC_NS_SMC_CMD));

    // set value to indicate if it is a return smc
    smc_out_data_ring[smc_out_pos_write].ret = ret;

    // if an agent_id is present - copy content of buffer
    if(smc_cmd->agent_id != 0x0)    {
        // test by printing agent buffers
        int i = 0;
        while(i < agent_count)  {
            //printk("agent_buffer: %d", i);
            //print_hex_dump_bytes("agent_buffer: ", DUMP_PREFIX_ADDRESS, agent_shared_mem_virt[i], 512);
            // allocate for agent_buffer on heap
            smc_out_data_ring[smc_out_pos_write].agent_buffers[i] = kmalloc(SZ_4K, GFP_KERNEL);
            if(!smc_out_data_ring[smc_out_pos_write].agent_buffers[i])  {
                printk("could not allocate on heap for agent buffer");
                spin_unlock_irqrestore(&write_out_lock, flags);
                return -EFAULT;
            }
            // copy content
            memcpy(smc_out_data_ring[smc_out_pos_write].agent_buffers[i], agent_shared_mem_virt[i], SZ_4K);
            i += 1;
        }
    }

    int original_smc_index = smc_out_pos_write;

    // in case we get a returning smc - we usually go one back
    if(ret == true) {
        // problem: in a return smc uuid_phys and operation_phys do not hold physical addresses but virtual addresses of inside TC
        // dirty workaround: get the last smc in the queue (its most likely the corresponding sent smc) and take the addresses from there
        // check if event_nr is the same
        unsigned int ret_smc_event_nr = smc_cmd->event_nr;
        original_smc_index = smc_out_pos_write - 1;
        if(original_smc_index < 0)  {
            original_smc_index = SMC_CMD_MAX_SIZE - 1;
        }
        printk("\nSMC_RET taking corresponding ret %x", original_smc_index);
        // get that for operation_phys and uuid_phys
        // careful if a param is a buffer the addresses will also be not correct
        smc_cmd = &smc_out_ring[original_smc_index];
        if(ret_smc_event_nr != smc_cmd->event_nr)    {
            printk("\nSMC_RET event numbers do not fit -> not correct SMC pair");
            // TODO: thats some sort of error but should rarely occur
            // increase pointer for next element wrap around max size
            //smc_out_pos_write = (smc_out_pos_write + 1) % SMC_CMD_MAX_SIZE;
            // release lock so next smc can be written
            spin_unlock_irqrestore(&write_out_lock, flags);
            return 0;
        }
    }
    // check if its a agent response and search for original sent smc
    while(smc_cmd->agent_id != 0x0)  {
        // go backwards in ring buffer
        original_smc_index = original_smc_index - 1;
        if(original_smc_index == smc_out_pos_write) {
            printk("\nSMC_AGENT no original smc found!");
            spin_unlock_irqrestore(&write_out_lock, flags);
            return 0;
        }
        if(original_smc_index < 0)  {
            original_smc_index = SMC_CMD_MAX_SIZE - 1;
        }
        smc_cmd = &smc_out_ring[original_smc_index];
    }

    // smc_cmd now points to the original smc in queue

    if(smc_cmd->uuid_phys)  {
        // get uuid content as hex ascii
        char *uuid = (char *) phys_to_virt(smc_cmd->uuid_phys);
        if(uuid)    {
            // uuid consists of 16 byte + 1 byte 
            unsigned int uuid_counter = 0;
            while(uuid_counter < 17)    {
                sprintf(smc_out_data_ring[smc_out_pos_write].uuid + (uuid_counter*2), "%02X", uuid[uuid_counter]);
                uuid_counter += 1;
            }
        }
    }

    // check if smc cmd has operations
    if(smc_cmd->operation_phys) {
        TC_NS_Operation *operation = phys_to_virt(smc_cmd->operation_phys);
        
        // read out TC Operations - might be null
        if(operation)   {
            // copy operation paramTypes
            //memcpy(&smc_out_data_ring[smc_out_pos_write].paramTypes, &operation->paramTypes, sizeof(unsigned int));
            smc_out_data_ring[smc_out_pos_write].paramTypes = operation->paramTypes;

            //go through all 4 parameters
            int j = 0;
            int curr_paramtype = 0;
            while(j < 4)    {
                // get current parameter
                curr_paramtype = TEEC_PARAM_TYPE_GET(operation->paramTypes, j);
                if(curr_paramtype == TEEC_VALUE_INPUT || curr_paramtype == TEEC_VALUE_INOUT || curr_paramtype == TEEC_VALUE_OUTPUT)   {
                    // this parameter has values - no memref
                    // copy values
                    smc_out_data_ring[smc_out_pos_write].params[j].value_a = operation->params[j].value.a;
                    smc_out_data_ring[smc_out_pos_write].params[j].value_b = operation->params[j].value.b;

                }
                else if(curr_paramtype == TEEC_MEMREF_TEMP_INPUT || curr_paramtype == TEEC_MEMREF_TEMP_INOUT || curr_paramtype == TEEC_MEMREF_TEMP_OUTPUT) {
                    // this parameter has memref - need to read out buffer with size
                    // we need at least the size for TEEC_MEMREF_TEMP_OUTPUT

                    // if we get a return smc we need to look at the backup addr in smc_param from queue
                    void *temp_buffer = NULL;
                    if(original_smc_index != smc_out_pos_write) {
                        // returning smc or agent smc - take buffer addr of original smc and dont save anything
                        temp_buffer = phys_to_virt(smc_out_data_ring[original_smc_index].params[j].real_phys_addr);
                    }
                    else    {
                        // normal sent smc - take current buffer addr and save it
                        temp_buffer = phys_to_virt(operation->params[j].memref.buffer);
                        smc_out_data_ring[smc_out_pos_write].params[j].real_phys_addr = operation->params[j].memref.buffer;
                    }
                    if (temp_buffer) {
                        // allocate for buffer and copy address
                        //smc_out_data_ring[smc_out_pos_write].params[j].value_a = (void *) __get_free_pages(GFP_KERNEL, get_order(ROUND_UP(operation->params[j].memref.size, SZ_4K)));
                        smc_out_data_ring[smc_out_pos_write].params[j].value_a = kmalloc(operation->params[j].memref.size, GFP_KERNEL);
                        // just set value for size
                        smc_out_data_ring[smc_out_pos_write].params[j].value_b = operation->params[j].memref.size;
                        if (!smc_out_data_ring[smc_out_pos_write].params[j].value_a)  {
                            printk("\nSMC_RET buffer heap alloc failed!");
                            printk("\nSMC_RET value_a: %x, value_b:%x", smc_out_data_ring[smc_out_pos_write].params[j].value_a, smc_out_data_ring[smc_out_pos_write].params[j].value_b);
                            spin_unlock_irqrestore(&write_out_lock, flags);
                            return -EFAULT;
                        }
                        // copy param content into buffer
                        memcpy(smc_out_data_ring[smc_out_pos_write].params[j].value_a, temp_buffer, operation->params[j].memref.size);
                    }
                }
                j += 1;
            }
        }
    }
    // increase pointer for next element wrap around max size
    smc_out_pos_write = (smc_out_pos_write + 1) % SMC_CMD_MAX_SIZE;
    // release lock so next smc can be written
    spin_unlock_irqrestore(&write_out_lock, flags);
    //only used for timing
    printk("\nSMC_TIMESTAMP end of write_out of uid %x with event_nr %d\n", smc_cmd->uid, smc_cmd->event_nr);
    return 0;
}

/*
    This function gets called if read from /proc/smc_forwarder
    Get SMC pointed to by 'smc_out_pos_read' in smc ring buffer and return it as hex ascii
*/
static ssize_t smc_forward_read(struct file *file, char *buffer, size_t length, loff_t *offset) {
    unsigned long flags = 0;
    unsigned long t = 0;
    // thats the size of the current smc cmd
    unsigned long out_buffer_size = 0;
    //check if new smc cmds are in queue - if not just wait
    while(smc_out_pos_write == smc_out_pos_read)    {
        t = msleep_interruptible(50);
        if(t != 0)  {
            return 0;
        }
    }
    printk("\nSTEST sending smc number %x", smc_out_pos_read);

    // get next smc cmd from queue
    TC_NS_SMC_CMD smc_cmd = smc_out_ring[smc_out_pos_read];
    // get corresponding data for that smc cmd
    struct smc_cmd_data smc_data = smc_out_data_ring[smc_out_pos_read];

    // a new smc starts
    if(smc_data.ret == true)    {
        const char *smc_start_indicate = "\nSMC_RETURN_START";
        out_buffer_size += sprintf(out_buffer + out_buffer_size, smc_start_indicate);
    }
    else    {
        const char *smc_start_indicate = "\nSMC_START";
        out_buffer_size += sprintf(out_buffer + out_buffer_size, smc_start_indicate);
    }
    //printk("\nSMC_RET starting new smc... with bool %d", smc_data.ret);

    // write smc cmd struct content itself + paramTypes for operation
    out_buffer_size += sprintf(out_buffer + out_buffer_size,
    "\nuuid:%s,uuid_phys:%x,cmd_id:%x,dev_file_id:%x,context_id:%x,agent_id:%x,operation_phys:%x,operation_paramTypes:%x,login_method:%x,login_data:%x,err_origin:%x,ret_val:%x,event_nr:%x,remap:%x,uid:%x,started:%x",
    smc_data.uuid, smc_cmd.uuid_phys, smc_cmd.cmd_id, smc_cmd.dev_file_id, smc_cmd.context_id, smc_cmd.agent_id, smc_cmd.operation_phys, 
    smc_data.paramTypes, smc_cmd.login_method, smc_cmd.login_data, smc_cmd.err_origin, smc_cmd.ret_val, smc_cmd.event_nr, smc_cmd.remap, smc_cmd.uid, smc_cmd.started);

    // go through each of the four parameters
    int paramIndex = 0;
    while(paramIndex < 4)   {
        int curr_paramtype = 0;
        curr_paramtype = TEEC_PARAM_TYPE_GET(smc_data.paramTypes, paramIndex);
        printk("\nSTEST param %x with value_a %x", paramIndex, smc_data.params[paramIndex].value_a);
        printk("\nSTEST param %x with value_b %x", paramIndex, smc_data.params[paramIndex].value_b);
        if(curr_paramtype == TEEC_VALUE_INPUT || curr_paramtype == TEEC_VALUE_INOUT || curr_paramtype == TEEC_VALUE_OUTPUT)   {
            out_buffer_size += sprintf(out_buffer + out_buffer_size, "\nparam_%x:value_a:%x,value_b:%x", paramIndex, (unsigned int) smc_data.params[paramIndex].value_a, (unsigned int) smc_data.params[paramIndex].value_b);
        }
        else if(curr_paramtype == TEEC_MEMREF_TEMP_INPUT || curr_paramtype == TEEC_MEMREF_TEMP_INOUT || curr_paramtype == TEEC_MEMREF_TEMP_OUTPUT) {
            // write size
            if(smc_data.params[paramIndex].value_a)  {
                out_buffer_size += sprintf(out_buffer + out_buffer_size, "\nparam_%x:size:%x,buffer:", paramIndex, (unsigned int)smc_data.params[paramIndex].value_b);
            // write hexstring of memory content
            // TODO: is it really necessary to convert it to a hexstring?
                unsigned int count = 0;
                while(count < (unsigned int)smc_data.params[paramIndex].value_b) {
                    // try with this commented out to see if the buffer is the problem
                    out_buffer_size += sprintf(out_buffer + out_buffer_size, "%02X", *(char *)(smc_data.params[paramIndex].value_a + count));
                    count += 1;
                }
            }
        }
        paramIndex += 1;
    }
    if(out_buffer_size > OUT_BUFFER_SIZE)   {
        //printk("\nSTEST buffer too small...");
        return -EFAULT;
    }

    // add shm buffer of agents if needed
    if(smc_cmd.agent_id != 0x0) {
        const char *shm_agent_start_indicate = "\nSHM_AGENT_START";
        const char *shm_agent_end_indicate = "\nSHM_AGENT_END\n";

        out_buffer_size += sprintf(out_buffer + out_buffer_size, shm_agent_start_indicate);
        int i = 0;
        while(i < agent_count)  {
            out_buffer_size += sprintf(out_buffer + out_buffer_size, "\nphys_addr:%02X\n", virt_to_phys(agent_shared_mem_virt[i]));
            unsigned int buffer_count = 0;
            while(buffer_count < SZ_4K) {
                out_buffer_size += sprintf(out_buffer + out_buffer_size, "%02X", *(char *)(smc_data.agent_buffers[i] + buffer_count));
                buffer_count += 1;
            }
            i += 1;
        }
        out_buffer_size += sprintf(out_buffer + out_buffer_size, shm_agent_end_indicate);
    }

    const char *smc_end_indicate = "\nSMC_END\n";
    out_buffer_size += sprintf(out_buffer + out_buffer_size, smc_end_indicate);

    printk("\nSTEST Total buffersize: %x, offset: %x, length: %x", out_buffer_size, *offset, length);
    // now the complete smc is inside out_buffer as hexstring

    // len is the size of the smc cmd as format string to be read
    size_t len = min(out_buffer_size - *offset, length);
    if (len <= 0)   {
        //printk("\nSTEST len <= 0");
        return 0;
    }
    printk("\nSTEST sending %x len bytes", len);
    
    // smc cmd fits in one buffer for read call
    if((len + *offset) >= out_buffer_size)    {
        //paramIndex = 0;
        // go through each parameter and free allocated data on heap
        // TODO fix this... freeing seems to be broken
        /*
        while(paramIndex < 4)   {
            int curr_paramtype = 0;
            curr_paramtype = TEEC_PARAM_TYPE_GET(smc_data.paramTypes, paramIndex);
            if(curr_paramtype == TEEC_VALUE_INPUT || curr_paramtype == TEEC_VALUE_INOUT)   {
                kfree(smc_data.params[paramIndex].value_a);
                kfree(smc_data.params[paramIndex].value_b);
            }
            else if(curr_paramtype == TEEC_MEMREF_TEMP_INPUT|| curr_paramtype == TEEC_MEMREF_TEMP_INOUT) {
                //TODO: make TEEC_MEMREF_TEMP_INOUT work
                __free_pages(smc_data.params[paramIndex].value_a, get_order(ROUND_UP(*(unsigned int *)smc_data.params[paramIndex].value_b, SZ_4K)));
                kfree(smc_data.params[paramIndex].value_b);
            }
            paramIndex += 1;
        }*/
        // go to next element in smc ring buffer
        smc_out_pos_read = (smc_out_pos_read + 1) % SMC_CMD_MAX_SIZE;
        // copy fmt string to userland
        if (copy_to_user(buffer, (out_buffer + *offset), len))    {
            return -EFAULT;
        }
        // as it is the last/only read call for that smc cmd reset offset 
        *offset = 0;
        //printk("\nSTEST sent complete reseting offset... read_pos %x", smc_out_pos_read);
    }
    else    {
        // copy fmt string to userland
        if (copy_to_user(buffer, (out_buffer + *offset), len))    {
            return -EFAULT;
        }
        // smc cmd does not fit into one buffer -> adjust offset for next read
        *offset += len;
    }
    return len;
}

/*
    This function gets called if written to /proc/smc_forwarder
    Used to send commands to the smc forwarder
    "smc_on"/"smc_off": activate/deactivate SMC execution on the phone
*/
static ssize_t smc_forward_write(struct file *file, char *buffer, size_t length, loff_t *offset) {
    const char* smc_add = "smc_add\0";
    const char* smc_off = "smc_off\0";
    const char* smc_on = "smc_on\0";
    const char* smc_forward_string = "smc_forward\0";
    unsigned long flags;
    if(strncmp(buffer, smc_add, strlen(smc_add)) == 0)   {
        spin_lock_irqsave(&smc_status_lock, flags);
        smc_exec_status += 1;
        printk("\nSMC_EXEC_STATUS added -> now %d", smc_exec_status);
        //only used for timing
        printk("\nSMC_TIMESTAMP add SMC received\n");
        spin_unlock_irqrestore(&smc_status_lock, flags);
        return strlen(smc_add);
    }
    else if(strncmp(buffer, smc_off, strlen(smc_off)) == 0)   {
        spin_lock_irqsave(&smc_status_lock, flags);
        smc_exec_status = 0;
        printk("\nSMC_EXEC_STATUS off -> no SMCs get executed anymore");
        spin_unlock_irqrestore(&smc_status_lock, flags);
        return strlen(smc_off);
    }
    else if(strncmp(buffer, smc_on, strlen(smc_on)) == 0)   {
        spin_lock_irqsave(&smc_status_lock, flags);
        smc_exec_status = -1;
        printk("\nSMC_EXEC_STATUS on -> SMCs executed normally");
        spin_unlock_irqrestore(&smc_status_lock, flags);
        return strlen(smc_on);
    }
    else if(strncmp(buffer, smc_forward_string, strlen(smc_forward_string)) == 0)   {
        spin_lock_irqsave(&smc_status_lock, flags);
        smc_forward = 1;
        printk("\nSMC_EXEC_STATUS forwarding active");
        spin_unlock_irqrestore(&smc_status_lock, flags);
        return strlen(smc_forward_string);
    }
    return length;
}

static int smc_forward_open(struct inode *inode, struct file *file) {
    return 0;
}

static int smc_forward_close(struct inode *inode, struct file *file) {
    return 0;
}

static struct file_operations smc_forward_file_ops = {
    .owner   = THIS_MODULE,
    .open    = smc_forward_open,
    .read    = smc_forward_read,
    .write   = smc_forward_write,
    .release = smc_forward_close
};


static int smc_forward_init(void)   {
    struct proc_dir_entry *entry;
    // register proc entry to read/write to
    entry = proc_create_data(DEVICE_NAME, 0, NULL, &smc_forward_file_ops, NULL);
    return 0;
}

static void smc_forward_exit(void)  {
    remove_proc_entry(DEVICE_NAME, NULL);
}


module_init(smc_forward_init);
module_exit(smc_forward_exit);