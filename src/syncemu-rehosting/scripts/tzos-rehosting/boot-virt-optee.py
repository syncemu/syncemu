import os
import sys

import click

from common import install_logging
from common.avatar2.convenience.optee.factories import OpteeQemuv8AvatarFactory, OpteeHiKey620AvatarFactory
from common.avatar2.convenience.optee.structs import OpteeMsgParam, OpteeMsgParamValue, OpteeMsgParamRmem, OpteeMsgArg


def uuid_to_param_value(hex_uuid: str):
    # convert hex string into a bytes object
    uuid = bytes.fromhex(hex_uuid)
    # the result should contain 16 bytes, i.e., 2 64-bit integers
    assert len(uuid) == 16

    # split into two 8-byte hex strings
    chunks = (uuid[:8], uuid[8:])

    # convert chunks to ints and unpack them into three variables
    a, b = (int.from_bytes(i, "little") for i in chunks)

    # c may be 0, apparently
    c = 0

    # build value from the three values
    return OpteeMsgParamValue(a, b, c)


def open_ta_session(hex_uuid: str):
    # set up to open a session for the hello world TA
    # reverse engineered from get_open_session_meta
    optee_msg_arg = OpteeMsgArg(
        # cmd = OPTEE_MSG_CMD_OPEN_SESSION
        0,
        # func = 0 (not used)
        0,
        # session = 0 (will be returned by this call, actually)
        0,
        # cancel_id = 0 (not used)
        0,
        # pad = 0 (not used)
        0,
        # ret = 0 (not used)
        0,
        # ret_origin = 0 (not used)
        0,
        # must pass 2 parameters, according to get_open_session_meta
        # both have to set attr to 0x101 = OPTEE_MSG_ATTR_META (0x100) | OPTEE_MSG_ATTR_TYPE_VALUE_INPUT (0x1)
        params=[
            # the first parameter transports the app's UUID in values a and b
            OpteeMsgParam(0x101, uuid_to_param_value(hex_uuid)),
            # the second parameter's c value is called clnt_id->login
            # for the hello world TA, the value is TEE_LOGIN_PUBLIC aka 0
            OpteeMsgParam(0x101, OpteeMsgParamValue(0, 0, 0)),
        ],
    )

    return optee_msg_arg


def close_ta_session(session: int):
    # set up to close a session for the TA
    # reverse engineered from optee_close_session (call.c)
    optee_msg_arg = OpteeMsgArg(
        # cmd = OPTEE_MSG_CMD_CLOSE_SESSION
        2,
        # func = OPTEE_MSG_ATTR_META (0x100) | OPTEE_MSG_ATTR_TYPE_VALUE_INPUT (0x1)
        0,
        # session is specified by user (who gets this from openSession())
        session,
        # cancel_id = 0 (not used)
        0,
        # pad = 0 (not used)
        0,
        # ret = 0 (not used)
        0,
        # ret_origin = 0 (not used)
        0,
        params=[],
    )

    return optee_msg_arg


def ta_invoke_increment_command(session: int, value: int):
    # # for the record: one could just read the shared memory buffer directly, too
    # # this however demonstrates the raw-mode support in the peripheral's read_memory method
    # shared_memory_content = self.qemu_target.read_memory(0x7D9A1000, 0x4 * 0x20, raw=True)
    # print(shared_memory_content)

    # set up to invoke hello world's increment command
    optee_msg_arg = OpteeMsgArg(
        # cmd = 1 (OPTEE_MSG_CMD_INVOKE_COMMAND)
        1,
        # func = 0 (TA_HELLO_WORLD_CMD_INC_VALUE)
        0,
        # session is specified by user (who gets this from openSession())
        session,
        # cancel_id = 0 (dont know? keep old value from openSession())
        0,
        # pad = 0 (dont know?)
        0,
        # ret = 0 (dont know?)
        0,
        # ret_origin = 2 (keep old value from openSession)
        2,
        [
            # param.attr = 3 (OPTEE_MSG_ATTR_TYPE_VALUE_INOUT)
            # param value a = value (will be incremented)
            OpteeMsgParam(3, OpteeMsgParamValue(value, 0, 0)),
        ],
    )

    return optee_msg_arg


def ta_invoke_generate_random_command(session: int, offset: int, number_of_bytes: int):
    # # for the record: one could just read the shared memory buffer directly, too
    # # this however demonstrates the raw-mode support in the peripheral's read_memory method
    # shared_memory_content = self.qemu_target.read_memory(0x7D9A1000, 0x4 * 0x20, raw=True)
    # print(shared_memory_content)

    # set up to invoke hello world's increment command
    optee_msg_arg = OpteeMsgArg(
        # cmd = 1 (OPTEE_MSG_CMD_INVOKE_COMMAND)
        1,
        # func = 0 (TA_RANDOM_CMD_GENERATE)
        0,
        # session is specified by user (who gets this from openSession())
        session,
        # cancel_id = 0 (dont know? keep old value from openSession())
        0,
        # pad = 0 (dont know?)
        0,
        # ret = 0 (dont know?)
        0,
        # ret_origin = 2
        2,
        [
            # param.attr = 6 (TEEC_MEMREF_TEMP_OUTPUT)
            # TODO: seems to fail in copy_in_params in optee core when compiled with no dyn shm
            # try 0xa = OPTEE_MSG_ATTR_TYPE_VALUE_OUTPUT instead?
            # param value offset = relative offset from address of this struct
            # param value size = number of bytes to be generated
            # param value shm_ref = 0 not sure why this must be the case or which function this value has
            OpteeMsgParam(0x6, OpteeMsgParamRmem(offset, number_of_bytes, 0x0)),
        ],
    )

    return optee_msg_arg


@click.command()
@click.argument("dtb_path")
@click.argument("bl32_path")
@click.argument("trusted_apps_dir")
@click.option("--avatar-output-dir", type=click.Path(exists=False))
@click.option("--image-type", type=str, default="QEMUv8")
def main(dtb_path, bl32_path, trusted_apps_dir, avatar_output_dir, image_type):
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
    if image_type == "QEMUv8":
        factory = OpteeQemuv8AvatarFactory()

    elif image_type == "HiKey620":
        factory = OpteeHiKey620AvatarFactory()

    else:
        print(f"Unknown image type: {image_type}")
        sys.exit(1)

    context = factory.get_rehosting_context(dtb_path, bl32_path, trusted_apps_dir, avatar_output_dir=avatar_output_dir)

    runner = factory.get_runner(context)

    # initialize configurable _after_ initializing every peripheral, as the latter adds some memory ranges, too
    context.avatar.init_targets()

    runner.cont()
    print("OP-TEE TZOS booted")

    # comment in if you want to run the hello world TA
    optee_msg_arg = runner.execute_tzos_command(open_ta_session("8aaaf200245011e4abe20002a5d5c51b"))
    #optee_msg_arg = runner.execute_tzos_command(open_ta_session("b6c53aba96694668a7f2205629d00f86"))
    assert optee_msg_arg.ret == 0x0, optee_msg_arg
    print(f"Session for TA opened, return msg: {optee_msg_arg}")

    # comment in if you want to execute increment for hello world TA
    optee_msg_arg = runner.execute_tzos_command(ta_invoke_increment_command(1, 200))

    """
    # randomTA seems to fail for now due to BAD_PARAMETER...
    # this seems to be an offset starting from the address of the optee_msg_arg struct
    offset_to_put_random_bytes = 0x100
    number_of_random_bytes = 0x20
    optee_msg_arg = runner.execute_tzos_command(
        ta_invoke_generate_random_command(1, offset_to_put_random_bytes, number_of_random_bytes)
    )
    assert optee_msg_arg.ret == 0x0, optee_msg_arg
    print("Random bytes generated")
    # the random bytes are put in memory at optee_msg_arg-struct + offset
    print(
        context.target.read_memory(
            context.shared_memory.address + offset_to_put_random_bytes,
            number_of_random_bytes,
            raw=True,
        )
    )
    """

    # the close session command seems to work fine for both TAs
    optee_msg_arg = runner.execute_tzos_command(close_ta_session(1))
    assert optee_msg_arg.ret == 0x0, optee_msg_arg
    print("Session for TA closed")


if __name__ == "__main__":
    main()
