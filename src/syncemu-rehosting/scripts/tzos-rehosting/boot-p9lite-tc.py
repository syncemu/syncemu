import os
import sys
import subprocess
import io
import csv
import click
import time

from subprocess import Popen, PIPE

from common import install_logging, get_logger
from common.avatar2.convenience.trustedcore.factories import TrustedCoreHuaweiP9LiteAvatarFactory
from common.avatar2.convenience.trustedcore.structs import TC_NS_SMC_CMD, TC_Operation, TC_Param
from common.avatar2.convenience.trustedcore.shared_memory_manager import SharedMemoryManager
from common.avatar2.convenience.trustedcore.trustedcore_boot_patcher import TrustedCoreBootPatcher


def register_agent(manager: SharedMemoryManager, agent_id: int):
    tc_op = TC_Operation(0x1000, [TC_Param(0x90000000, 0x1000)])

    uuid_phys = manager.allocate_bytes(bytes.fromhex("0100000000000000000000000000000000"))
    operation_phys = manager.allocate_bytes(tc_op.to_bytes())
    tc_ns_smc_cmd = TC_NS_SMC_CMD(
        # uuid_phys: physical address that points to uuid
        uuid_phys,
        # cmd_id: here 0x6 for register_agent
        0x6,
        # dev_file_id: ?
        0x0,
        # context_id: ?
        0x0,
        # agent_id: given as parameter
        agent_id,
        # operation_phys: physical address that points to TC_Operation struct
        operation_phys,
        # login_method: 0x7 for TEEC_LOGIN_IDENTIFY
        0x7,
        # login_data: ?
        0x0,
        # err_origin: ?
        0x0,
        # ret_val: ?
        0x0,
        # event_nr: ?
        0x0,
        # remap: ?
        0x0,
        # uid: ?
        0x0,
        # started: ?
        0x0,
    )

    return tc_ns_smc_cmd


def open_ta_session(manager: SharedMemoryManager, hex_uuid: str):
    uid_address = manager.allocate_bytes(0x3F9 .to_bytes(4, "little"))
    ta_path_address = manager.allocate_bytes(b"/system/bin/keystore")
    tc_op = TC_Operation(
        0x5502, [TC_Param(0x0, 0x0), TC_Param(0x0, 0x0), TC_Param(uid_address, 0x4), TC_Param(ta_path_address, 0x29)]
    )

    uuid_phys = manager.allocate_bytes(bytes.fromhex(hex_uuid))
    operation_phys = manager.allocate_bytes(tc_op.to_bytes())
    tc_ns_smc_cmd = TC_NS_SMC_CMD(
        # uuid_phys: physical address that points to uuid
        uuid_phys,
        # cmd_id: here 0x2 for open session
        0x2,
        # dev_file_id: ?
        0x0,
        # context_id: ?
        0x0,
        # agent_id: dont need here
        0x0,
        # operation_phys: physical address that points to TC_Operation struct
        operation_phys,
        # login_method: 0x7 for TEEC_LOGIN_IDENTIFY
        0x7,
        # login_data: ?
        0x0,
        # err_origin: ?
        0x0,
        # ret_val: ?
        0x0,
        # event_nr: ?
        0x0,
        # remap: ?
        0x0,
        # uid: id of keystored
        1017,
        # started: ?
        0x0,
    )

    return tc_ns_smc_cmd


def invoke_ta_command(manager: SharedMemoryManager, tc_ns_smc_cmd_return: TC_NS_SMC_CMD):

    # as the paramTypes expect an address just generate a random
    # maybe need to fill with "real" data
    test_address = manager.allocate_bytes(0x1234 .to_bytes(4, "little"))
    tc_op = TC_Operation(
        0x0026, [TC_Param(test_address, 0x10), TC_Param(0x0, 0x0), TC_Param(0x0, 0x0), TC_Param(0x0, 0x0)]
    )

    # first byte MUST be zero -> cmd_id is interpreted by the TA
    uuid_phys = manager.allocate_bytes(bytes.fromhex("0007070707070707070707070707070707"))
    operation_phys = manager.allocate_bytes(tc_op.to_bytes())
    tc_ns_smc_cmd = TC_NS_SMC_CMD(
        # uuid_phys: physical address that points to uuid
        uuid_phys,
        # cmd_id: first byte of uuid must be 0 so this will be interpreted by the TA
        # 0x6 will call km_init_ability
        0x6,
        # dev_file_id: ?
        0x0,
        # context_id: that is the session_id
        tc_ns_smc_cmd_return.context_id,
        # agent_id: dont need here
        0x0,
        # operation_phys: physical address that points to TC_Operation struct
        operation_phys,
        # login_method: 0x7 for TEEC_LOGIN_IDENTIFY
        0x7,
        # login_data: ?
        0x0,
        # err_origin: ?
        0x0,
        # ret_val: ?
        0x0,
        # event_nr: ?
        0x0,
        # remap: ?
        0x0,
        # uid: id of keystored
        1017,
        # started: ?
        0x0,
    )

    return tc_ns_smc_cmd


def set_registers(context, regs):
    # go through each register and set it if needed
    for i in range(len(regs)):
        # get value
        regs[i] = int(regs[i].split(b":")[-1], 16)
    # print(regs)
    # set general purpose regs
    context.target.write_register("x0", regs[0])
    context.target.write_register("x1", regs[1])
    context.target.write_register("x2", regs[2])
    context.target.write_register("x3", regs[3])
    context.target.write_register("x4", regs[4])
    context.target.write_register("x5", regs[5])
    context.target.write_register("x6", regs[6])
    context.target.write_register("x7", regs[7])
    context.target.write_register("x8", regs[8])
    context.target.write_register("x9", regs[9])
    context.target.write_register("x10", regs[10])
    context.target.write_register("x11", regs[11])
    context.target.write_register("x12", regs[12])
    context.target.write_register("x13", regs[13])
    context.target.write_register("x14", regs[14])
    context.target.write_register("x15", regs[15])
    context.target.write_register("x16", regs[16])
    context.target.write_register("x17", regs[17])
    context.target.write_register("x18", regs[18])
    context.target.write_register("x19", regs[19])
    context.target.write_register("x20", regs[20])
    context.target.write_register("x21", regs[21])
    context.target.write_register("x22", regs[22])
    context.target.write_register("x23", regs[23])
    context.target.write_register("x24", regs[24])
    context.target.write_register("x25", regs[25])
    context.target.write_register("x26", regs[26])
    context.target.write_register("x27", regs[27])
    context.target.write_register("x28", regs[28])
    context.target.write_register("x29", regs[29])
    context.target.write_register("x30", regs[30])

    # set system regs
    # these will be set to the corresponding system regs in execute tzos command
    context.smc_spsr_register_value = regs[34]
    context.tzos_eret_entrypoint = regs[35]

    context.write_system_register("sp_el0", regs[31])
    context.write_system_register("scr_el3", regs[32])
    context.write_system_register("spsr_el1", regs[36])
    context.write_system_register("elr_el1", regs[37])
    context.write_system_register("spsr_irq", regs[40])
    context.write_system_register("sctlr_el1", regs[42])
    context.write_system_register("cpacr_el1", regs[44])
    context.write_system_register("ttbr0_el1", regs[48])
    context.write_system_register("ttbr1_el1", regs[49])
    context.write_system_register("tcr_el1", regs[52])
    context.write_system_register("dacr32_el2", regs[56])
    context.write_system_register("contextidr_el1", regs[62])
    context.write_system_register("vbar_el1", regs[63])
    context.write_system_register("fpexc32_el2", regs[64])

    return

def parse_and_inject_shm_agent_buffers(context, session):
    print("Starting to inject shm of agents")
    while session.poll() is None:
        line = session.stdout.readline().split(b"\r")[0]
        if b"phys_addr:" in line:
            addr = int(line.split(b"\n")[0].split(b":")[-1], 16)
            # get content
            content = session.stdout.readline().split(b"\r")[0]
            memory_to_write = bytes.fromhex(content.decode())
            context.target.write_memory(addr, len(memory_to_write), memory_to_write, raw=True)

        if b"SHM_AGENT_END" in line:
            print("shm of agents injected")
            return
    return


total_smc_recv_time : float = 0
"""
    Parse the next SMC from the adb session
    @param session: the adb session to read from
    @return (smc cmd, uuid, operation, returning_smc)
"""
def recv_until_smc_ready(context, session):
    # init structs
    tc_ns_smc_device = TC_NS_SMC_CMD(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    tc_ns_op = TC_Operation(0x0, [TC_Param(0x0, 0x0), TC_Param(0x0, 0x0), TC_Param(0x0, 0x0), TC_Param(0x0, 0x0)])
    # in general we get a sending smc
    returning_smc = 0
    # the uuid content
    uuid_content = bytes()
    # params content
    params = [bytes(), bytes(), bytes(), bytes()]
    start_time = 0
    global total_smc_recv_time

    while session.poll() is None:
        line = session.stdout.readline().split(b"\r")[0]
        # we only need to inject shm agent if its a sent smc
        #if b"SHM_AGENT_START" in line and returning_smc == 0:
        #    parse_and_inject_shm_agent_buffers(context, session)
        # check if line has smc cmd
        if b"SMC_END" in line:
            total_smc_recv_time += time.time() - start_time
            # end for that smc cmd return it
            #tc_ns_smc_device.operation_phys = shm_manager.allocate_bytes(tc_ns_op.to_bytes())
            return tc_ns_smc_device, uuid_content, tc_ns_op, params, returning_smc

        elif b"SMC_RETURN_START" in line:
            # thats a returning smc
            returning_smc = 1
        elif b"uuid" in line:
            start_time = time.time()
            # reset if new struct begins
            tc_ns_smc_device = TC_NS_SMC_CMD(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            tc_ns_op = TC_Operation(
                0x0, [TC_Param(0x0, 0x0), TC_Param(0x0, 0x0), TC_Param(0x0, 0x0), TC_Param(0x0, 0x0)]
            )
            # now in that line should be everything for smc cmd
            smc_attrs = line.split(b",")
            # go through each attr and set value
            for attr in smc_attrs:
                curr_attr = attr.split(b":")
                if b"operation_paramTypes" == curr_attr[0]:
                    setattr(tc_ns_op, "paramTypes", int(curr_attr[-1].decode("utf-8"), 16))
                    # print(tc_ns_op)
                    continue
                elif b"uuid" == curr_attr[0]:
                    uuid_content = bytes.fromhex(curr_attr[-1].decode())
                    #tc_ns_smc_device.uuid_phys = shm_manager.allocate_bytes(uuid_read)
                    continue
                #elif b"uuid_phys" == curr_attr[0]:
                    # ignore that we set our own address
                #    continue
                # [0] is name and [1] is value
                setattr(tc_ns_smc_device, curr_attr[0].decode("utf-8"), int(curr_attr[-1].decode("utf-8"), 16))
                # print(tc_ns_smc_device)
        elif b"param_" in line:
            # get index first
            index = int(line.split(b":")[0].split(b"_")[-1].decode("utf-8"))
            # then get value a and value b
            value_a = line.split(b",")[0].split(b":")[1:]
            value_b = line.split(b",")[-1].split(b":")
            #print(value_a)
            #print(value_b[-1])
            if b"value" in value_a[0] and b"value" in value_b[0]:
                tc_ns_op.params[index].a = int(value_a[-1].decode("utf-8"), 16)
                tc_ns_op.params[index].b = int(value_b[-1].decode("utf-8"), 16)
            elif b"size" in value_a[0] and b"buffer" in value_b[0]:
                # set size careful its b in struct
                tc_ns_op.params[index].b = int(value_a[-1].decode("utf-8"), 16)
                bytes_read = bytes.fromhex(value_b[-1].decode())
                #tc_ns_op.params[index].a = shm_manager.allocate_bytes(bytes_read)
                #tc_ns_op.params[index].a = bytes_read
                params[index] = bytes_read
            # print(tc_ns_op)
    return None, None, None, None, None

def inject_smc_data_into_memory(shm_manager: SharedMemoryManager, uuid: bytes, operation: TC_Operation, params_content) -> (int, int):
    uuid_addr = 0
    operation_addr = 0
    # write uuid content
    uuid_addr = shm_manager.allocate_bytes(uuid)
    paramTypes = hex(operation.paramTypes)[2:].zfill(4)
    # go through each parameter and allocate if memory ref
    for i in range(len(operation.params)):
        # go through each param and check if its a buffer
        if paramTypes[len(operation.params) - i - 1] == "5" or paramTypes[len(operation.params) - i - 1] == "6" or \
                paramTypes[len(operation.params) - i - 1] == "7":
            operation.params[i].a = shm_manager.allocate_bytes(params_content[i])

    operation_addr = shm_manager.allocate_bytes(operation.to_bytes())

    return uuid_addr, operation_addr

def log_smc_to_history_file(smc_history_file, smc_cmd: TC_NS_SMC_CMD, uuid: bytes, operation: TC_Operation, params_content, smc_returning: int):

    if smc_returning == 0:
        smc_history_file.write("\nRECEIVED SMC FROM DEVICE:\n")
    elif smc_returning == 1:
        smc_history_file.write("\nRETURN FROM DEVICE:\n")
    elif smc_returning == -1:
        smc_history_file.write("\nRETURN FROM EMULATOR:\n")
    smc_history_file.write(smc_cmd.__repr__())
    print(smc_cmd)
    smc_history_file.write(f"\nuuid:{bytes.hex(uuid)}\n")
    smc_history_file.write(operation.__repr__())
    paramTypes = hex(operation.paramTypes)[2:].zfill(4)
    for i in range(len(operation.params)):
        # go through each param and check if its a buffer
        if paramTypes[len(operation.params) - i - 1] == "5" or paramTypes[len(operation.params) - i - 1] == "6" or \
                paramTypes[len(operation.params) - i - 1] == "7":
            smc_history_file.write(f"\nparam_{i}:{bytes.hex(params_content[i])}")
    smc_history_file.flush()
    return

def recover_smc_data_from_memory(sent_smc_cmd: TC_NS_SMC_CMD, sent_operation: TC_Operation, context):

    uuid_content = context.target.read_memory(sent_smc_cmd.uuid_phys, 17, raw=True)
    operation = TC_Operation.from_memory(context.target, sent_smc_cmd.operation_phys)
    # params content
    params = [bytes(), bytes(), bytes(), bytes()]

    paramTypes = hex(operation.paramTypes)[2:].zfill(4)
    for i in range(len(operation.params)):
        # go through each param and check if its a buffer
        if paramTypes[len(operation.params) - i - 1] == "6" or paramTypes[len(operation.params) - i - 1] == "7" or paramTypes[len(operation.params) - i - 1] == "5":
            params[i] = context.target.read_memory(sent_operation.params[i].a, operation.params[i].b, raw=True)

    return uuid_content, operation, params

def evaluate_and_write_to_file(smc_compare_writer, boot_patcher: TrustedCoreBootPatcher, uuid, DSW_smc_cmd: TC_NS_SMC_CMD, RSW_smc_cmd: TC_NS_SMC_CMD, DSW_operation: TC_Operation, RSW_operation: TC_Operation, DSW_params_content, RSW_params_content) -> int:
    # log smc to csv file
    # user action | event_nr | uuid/target task | cmd_id | smc_cmd | same? | param_size | same? | params_content | same? | accuracy_score | emulator_uart
    # check if event_nr are equivalent
    if DSW_smc_cmd.event_nr != RSW_smc_cmd.event_nr or DSW_smc_cmd.cmd_id != RSW_smc_cmd.cmd_id or DSW_operation.paramTypes != RSW_operation.paramTypes:
        print("Trying to compare different SMCs!")
        return -1

    # compare smc cmds
    # relevant attributes are: ret_val, err_origin, context_id, agent_id
    smc_cmd_write_DSW = f"{hex(DSW_smc_cmd.ret_val)}, {hex(DSW_smc_cmd.err_origin)}, {hex(DSW_smc_cmd.context_id)}, {hex(DSW_smc_cmd.agent_id)}"
    smc_cmd_write_RSW = f"{hex(RSW_smc_cmd.ret_val)}, {hex(RSW_smc_cmd.err_origin)}, {hex(RSW_smc_cmd.context_id)}, {hex(RSW_smc_cmd.agent_id)}"
    smc_cmd_same = 0
    if smc_cmd_write_DSW == smc_cmd_write_RSW:
        smc_cmd_same = 1

    # compare parameters
    # relevant are value, size, and buffer content

    size_DSW = ""
    size_RSW = ""
    size_same = 0
    content_DSW = ""
    content_RSW = ""
    content_same = 0

    paramTypes = hex(DSW_operation.paramTypes)[2:].zfill(4)
    for i in range(len(DSW_operation.params)):
        # go through each param and check if its a buffer
        if paramTypes[len(DSW_operation.params) - i - 1] == "6" or paramTypes[len(DSW_operation.params) - i - 1] == "7":
            # memref content and size
            size_DSW += hex(DSW_operation.params[i].b) + ","
            size_RSW += hex(RSW_operation.params[i].b) + ","

            content_DSW += bytes.hex(DSW_params_content[i]) + "\n"
            content_RSW += bytes.hex(RSW_params_content[i]) + "\n"

        elif paramTypes[len(DSW_operation.params) - i - 1] == "2" or paramTypes[len(DSW_operation.params) - i - 1] == "3":
            # values
            content_DSW += hex(DSW_operation.params[i].a) + "," + hex(DSW_operation.params[i].b) + "\n"
            content_RSW += hex(RSW_operation.params[i].a) + "," + hex(RSW_operation.params[i].b) + "\n"

    if size_DSW == size_RSW:
        size_same = 1

    if content_DSW == content_RSW:
        content_same = 1

    accuracy = int((smc_cmd_same + size_same + content_same) * 100 / 3)

    emu_uart = ""
    try:
        with open("/out/emulator_uart", "r") as emulator_uart:
            lines = emulator_uart.readlines()
            i = 5
            for l in lines[::-1]:
                emu_uart = l + emu_uart
                i -= 1
                if i <= 0:
                    break
    except:
        print("Make sure to write emulator uart to /out/emulator_uart")

    row_to_write = ["", hex(DSW_smc_cmd.event_nr), "0x"+bytes.hex(uuid), hex(DSW_smc_cmd.cmd_id), smc_cmd_write_DSW + "\n--------\n" + smc_cmd_write_RSW, smc_cmd_same, size_DSW + "\n--------\n" + size_RSW, size_same, content_DSW + "\n--------\n" + content_RSW, content_same, accuracy, emu_uart]
    smc_compare_writer.writerow(row_to_write)
    return 0

@click.command()
@click.argument("teeos_dump_path")
@click.option("--ca_in_the_loop")
@click.option("--avatar-output-dir", type=click.Path(exists=False))
def main(teeos_dump_path, ca_in_the_loop, avatar_output_dir):
    # hide spam of avatar2, pygdbmi and all that stuff
    # also, set up some colors, which make reading logs a lot easier
    # note that we intentionally disable avatar2's own logging below, as it conflicts with this setup
    # most likely, the avatar2 logging configuration is flawed, since it causes issues with our own logging
    install_logging()

    if avatar_output_dir:
        print("Using output dir {} with avatar2".format(avatar_output_dir), file=sys.stderr)

        # create directory if it doesn't exist
        # that saves the user from creating it beforehand
        os.makedirs(avatar_output_dir, exist_ok=True)

    # we're using a system of factories to instantiate and configure all the required objects
    # here, we decide which one to use
    # this follows the abstract factory pattern, as all factories inherit from an abstract class, and share the same
    # interface
    # at the moment, we only have binaries for the Huawei P9 Lite
    factory = TrustedCoreHuaweiP9LiteAvatarFactory()

    context = factory.get_rehosting_context(teeos_dump_path, avatar_output_dir)

    # initialize configurable _after_ initializing the SM emulator, as the latter adds some memory ranges, too
    context.avatar.init_targets()

    runner = factory.get_runner(context)
    # make sure to get boot patcher
    breakpoint_iterator = iter(runner._runner._breakpoint_handlers)
    boot_patcher = None
    while type(boot_patcher) is not TrustedCoreBootPatcher:
        boot_patcher = next(breakpoint_iterator)

    shm_manager = SharedMemoryManager(context)

    call_strategy = runner._call_into_tzos_strategy

    runner.cont()
    print("TrustedCore booted!")
    print(context.colored_register_printer.print_registers())

    if ca_in_the_loop == "on":
        # activate smc forwarding
        subprocess.Popen(["adb", "shell", "su -c 'echo 'smc_forward' > /proc/smc_forwarder'"], stdout=PIPE)

        # open session to read data
        session = subprocess.Popen(["adb", "shell", "su -c 'cat /proc/smc_forwarder'"], stdout=PIPE)

        # execute next smc on device
        subprocess.Popen(["adb", "shell", "su -c 'echo 'smc_add' > /proc/smc_forwarder'"], stdout=PIPE)

        # open file to save smc history
        smc_history_file = open("/out/smc_history", "w")
        # open csv file to save smc comparison evaluation
        csv_smc = open("/out/smc_compare.csv", "w", newline='')
        smc_compare_writer = csv.writer(csv_smc)
        # user action | event_nr | uuid/target task | cmd_id | smc_cmd | same? | param_size | same? | params_content | same? | accuracy_score | emulator_uart
        smc_compare_writer.writerow(['user action', 'event_nr', 'uuid / target task', 'cmd_id', 'smc_cmds', 'same?', 'param_sizes', 'same?', 'params_contents', 'same?', 'accuracy_score', 'emulator_uart'])
        csv_smc.flush()
        original_smc_cmd = None
        original_operation = None
        last_agent_cmd = None

        # for timing
        total_smc_inject_time : float = 0
        total_smc_exec_time : float = 0
        number_of_smc_received: int = 0
        global total_smc_recv_time

        while True:
            # reset shared memory used for parameter content and uuid
            shm_manager.next_unused_address = shm_manager.start_address
            
            """
                Workflow:
                parse sent smc
                    if not agent smc
                        inject into memory
                    if agent smc
                        set sent smc to ret agent smc and sync shared mem
                parse recv smc - do not put anything into memory
                exec sent smc
                    if agent smc
                        save for next sent smc
            """

            # receive sent SMC from NW of device - DNW
            DNW_smc_cmd, DNW_uuid, DNW_operation, DNW_params_content, DNW_smc_returning = recv_until_smc_ready(context, session)
            number_of_smc_received += 1
            log_smc_to_history_file(smc_history_file, DNW_smc_cmd, DNW_uuid, DNW_operation, DNW_params_content, DNW_smc_returning)

            # thats an sending SMC which is not part of agent -> we want that to be sent to the emulator
            if DNW_smc_returning == 0 and DNW_smc_cmd.agent_id == 0x0 and DNW_smc_cmd.uuid_phys != 0x0:
                # a sending non-agent smc should be injected into memory using shared memory manager
                start_time = time.time()
                DNW_smc_cmd.uuid_phys, DNW_smc_cmd.operation_phys = inject_smc_data_into_memory(shm_manager, DNW_uuid, DNW_operation, DNW_params_content)
                total_smc_inject_time += time.time() - start_time
                # set received SMC as original smc
                original_smc_cmd = DNW_smc_cmd
                original_operation = DNW_operation
            else:
                # thats an agent smc we do not want to send
                print("FAILURE! - SKIP")
                subprocess.Popen(["adb", "shell", "su -c 'echo 'smc_add' > /proc/smc_forwarder'"], stdout=PIPE)
                return

            # receive return SMC from SW of device - DSW
            DSW_smc_cmd, DSW_uuid, DSW_operation, DSW_params_content, DSW_smc_returning = recv_until_smc_ready(context, session)
            log_smc_to_history_file(smc_history_file, DSW_smc_cmd, DSW_uuid, DSW_operation, DSW_params_content, DSW_smc_returning)

            # all these smcs are agent relevant only - or a sending smc we do not want
            # receive until we get the real returning smc
            while DSW_smc_cmd.ret_val == 0xffff2001:
                print("Received agent return smc - SKIP")
                subprocess.Popen(["adb", "shell", "su -c 'echo 'smc_add' > /proc/smc_forwarder'"], stdout=PIPE)
                # receive sending
                DSW_smc_cmd, DSW_uuid, DSW_operation, DSW_params_content, DSW_smc_returning = recv_until_smc_ready(context, session)
                log_smc_to_history_file(smc_history_file, DSW_smc_cmd, DSW_uuid, DSW_operation, DSW_params_content, DSW_smc_returning)
                # receive returning
                DSW_smc_cmd, DSW_uuid, DSW_operation, DSW_params_content, DSW_smc_returning = recv_until_smc_ready(context, session)
                log_smc_to_history_file(smc_history_file, DSW_smc_cmd, DSW_uuid, DSW_operation, DSW_params_content, DSW_smc_returning)
                continue

            # execute DNW SMC and get return of emulator - RSW
            smc_to_exec = DNW_smc_cmd
            #if last_agent_cmd is not None:
            #    smc_to_exec = last_agent_cmd
            start_time = time.time()
            RSW_smc_cmd = runner.execute_tzos_command(smc_to_exec)
            total_smc_exec_time += time.time() - start_time
            RSW_smc_returning = -1
            # the corresponding data is found in memory in relation to the sent smc cmd and operation
            start_time = time.time()
            RSW_uuid, RSW_operation, RSW_params_content = recover_smc_data_from_memory(original_smc_cmd, original_operation, context)
            total_smc_inject_time += time.time() - start_time
            log_smc_to_history_file(smc_history_file, RSW_smc_cmd, RSW_uuid, RSW_operation, RSW_params_content, RSW_smc_returning)

            evaluate_and_write_to_file(smc_compare_writer, boot_patcher, DNW_uuid, DSW_smc_cmd, RSW_smc_cmd, DSW_operation, RSW_operation, DSW_params_content, RSW_params_content)
            csv_smc.flush()

            # execute next smc on device
            subprocess.Popen(["adb", "shell", "su -c 'echo 'smc_add' > /proc/smc_forwarder'"], stdout=PIPE)

            print(f"SMCs forwarded: {number_of_smc_received}, median_smc_recv: {total_smc_recv_time/number_of_smc_received}, median_smc_inject: {total_smc_inject_time/number_of_smc_received}, median_smc_exec: {total_smc_exec_time/number_of_smc_received}")

            continue
    else:
        # we do not use ca-in-the-loop
        # agent_socket_id
        tc_ns_smc = runner.execute_tzos_command(register_agent(shm_manager, 0x69E85664))
        print(tc_ns_smc)
        # agent_rpmb_id
        tc_ns_smc = runner.execute_tzos_command(register_agent(shm_manager, 0x4ABE6198))
        print(tc_ns_smc)
        print("Agents registered!")
        print(context.colored_register_printer.print_registers())

        # tc_ns_smc = runner.execute_tzos_command(open_ta_session("0102020202020202020202020202020202"))
        tc_ns_smc_input = open_ta_session(shm_manager, "0107070707070707070707070707070707")
        tc_ns_smc = runner.execute_tzos_command(tc_ns_smc_input)

        print(tc_ns_smc)
        print(TC_Operation.from_memory(context.target, tc_ns_smc_input.operation_phys))

        # print(context.colored_register_printer.print_registers())
        print("TA session opened!")

        tc_ns_smc_input = invoke_ta_command(shm_manager, tc_ns_smc)
        tc_ns_smc = runner.execute_tzos_command(tc_ns_smc_input)
        print(tc_ns_smc)
        print(TC_Operation.from_memory(context.target, tc_ns_smc_input.operation_phys))
        print("TA command invoked!")

    

if __name__ == "__main__":
    main()
