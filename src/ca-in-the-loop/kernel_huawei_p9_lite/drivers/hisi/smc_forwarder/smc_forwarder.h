#include <linux/types.h>


#include "../tzdriver/teek_ns_client.h"

#define DEVICE_NAME "smc_forwarder"

/*  IDEA: be able to use one of these functions at any point in kernel
        to get smc data IN and OUT of it
    1. Kernel gets ioctl and prepares SMC cmd struct
    2. call smc_write_out() which will put smc data in a queue
    3. kernel does SMC (optional if SMC execution is active)
    4. after SMC wait by calling smc_read_in()
    5. if smc data in queue ready get it and save values in memory
    6. continue execution and return to userland
*/

struct smc_param {
    void *value_a;
    void *real_phys_addr;
    void *value_b;
};

struct smc_cmd_data {
    bool ret;
    unsigned int paramTypes;
    struct smc_param params[4];
    char uuid[34];
    void *agent_buffers[5];
};

/*
    Use this function at any point in tzdriver if you want to save/forward the smc cmd into the ring buffer
    @param the smc cmd struct to be saved
    @param bool that indicates if it is a return smc
    Also allocates space for every smc data like TC_Operation parameter on the heap 
    We NEED to read out and save the smc data here, later it will be gone
*/
int smc_write_out(TC_NS_SMC_CMD *smc_cmd, bool ret);

/*
    Use this function at any point in tzdriver code if you want to be able to stop SMCs to get executed
    Check in a loop if SMCs should get executed or not by accessing 'smc_exec_status' with a lock
    TODO: can be used to inject a SMC cmd struct into tzdriver
    TODO: can be used to pause execution so a snapshot of the TZOS can be taken
    @return the smc cmd struct to be injected
*/
TC_NS_SMC_CMD *smc_read_in();