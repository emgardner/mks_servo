from .utils import u16s_to_i48, u16s_to_i32
import pymodbus.client as ModbusClient
import struct
import time
from .registers import InputRegisters, HoldingRegisters


class ZeroStatus:
    ZERO_IN_PROGRESS = 0
    ZERO_SUCCESS = 1
    ZERO_FAILURE = 2


class WorkMode:
    CR_OPEN = 0
    CR_CLOSE = 1
    CR_vFOC = 2
    SR_OPEN = 3
    SR_CLOSE = 4
    SR_vFOC = 5


class MotorRotation:
    CW = 0
    CCW = 1


class MotorStatus:
    MOTOR_FAILURE = 0  # read fail.
    MOTOR_STOP = 1  # motor stop
    MOTOR_SPEED_UP = 2  # motor speed up
    MOTOR_SPEED_DOWN = 3  # motor speed down
    MOTOR_FULL_SPEED = 4  # motor full speed
    MOTOR_HOMING = 5  # motor is homing
    MOTOR_CAL = 6  # motor is Cal…


class EnableActiveLevel:
    ACTIVE_LOW = 0
    ACTIVE_HIGH = 1
    ACTIVE_ALWAYS = 2


class Baudrate:
    BAUD_9600 = 0x01
    BAUD_19200 = 0x02
    BAUD_25000 = 0x03
    BAUD_38400 = 0x04
    BAUD_57600 = 0x05
    BAUD_115200 = 0x06
    BAUD_256000 = 0x07


class HomeTrigger:
    LOW = 0x00
    HIGH = 0x01


class EndLimit:
    DISABLE = 0x00
    ENABLE = 0x01


class Enabled:
    DISABLE = 0x00
    ENABLE = 0x01


class Servo(object):
    """
    Modbus Driver for MKS SERVO42C
    https://github.com/makerbase-motor/MKS-SERVO57D/blob/master/User%20Manual/MKS%20SERVO42%2657D_RS485%20User%20Manual%20V1.0.4.pdf
    """

    def __init__(self, port: str, address: int = 1):
        # Refactor these to be set during initialization
        self.client = ModbusClient.ModbusSerialClient(
            port,
            baudrate=38400,
            bytesize=8,
            parity="N",
            stopbits=1,
        )
        self._address = address

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, address: int):
        self._address = address

    def _write_registers(self, address: int, registers: list[int]):
        return self.client.write_registers(address, registers, slave=self._address)

    def _write_register(self, address: int, value: int):
        return self.client.write_register(address, value, slave=self._address)

    def _read_input_registers(self, address: int, quantity: int):
        return self.client.read_input_registers(address, quantity, slave=self._address)

    def set_work_mode(self, work_mode: WorkMode):
        return self._write_register(HoldingRegisters.SET_WORK_MODE, work_mode)

    def go_to_position(
        self,
        acceleration: int,
        velocity: int,
        pulses: int,
    ) -> int:
        pulses_bytes = struct.pack(">i", pulses)
        hi_bytes = struct.unpack(">H", pulses_bytes[:2])
        lo_bytes = struct.unpack(">H", pulses_bytes[2:])
        return self._write_registers(
            HoldingRegisters.MOVE_ABSOLUTE_PULSES,
            [acceleration, velocity, hi_bytes[0], lo_bytes[0]],
        )

    def go_to_axis_position(
        self,
        acceleration: int,
        velocity: int,
        pulses: int,
    ) -> int:
        pulses_bytes = struct.pack(">i", pulses)
        hi_bytes = struct.unpack(">H", pulses_bytes[:2])
        lo_bytes = struct.unpack(">H", pulses_bytes[2:])
        return self._write_registers(
            HoldingRegisters.MOVE_ABSOLUTE_AXIS,
            [acceleration, velocity, hi_bytes[0], lo_bytes[0]],
        )

    def get_error_angle(self) -> int:
        return self._read_input_registers(InputRegisters.ERROR_ANGLE, 2)

    def get_motor_status(self) -> MotorStatus:
        return self._read_input_registers(InputRegisters.MOTOR_STATUS, 1).registers[0]

    def wait_for_move_finished(self):
        # Add timeout
        while self.get_motor_status() != MotorStatus.MOTOR_STOP:
            time.sleep(0.1)

    def get_encoder_value_addition(self) -> int:
        value = self._read_input_registers(
            InputRegisters.ENCODER_ADDITION_VALUE, 3
        ).registers
        return u16s_to_i48(value[0], value[1], value[2])

    def set_work_current(self, value: int):
        return self._write_register(HoldingRegisters.SET_WORK_CURRENT, value)

    def set_hold_current(self, value: int):
        return self._write_register(HoldingRegisters.SET_HOLD_CURRENT, value)

    def set_home_param(
        self,
        home_trigger: HomeTrigger,
        home_direction: MotorRotation,
        home_speed: int,
        home_end_limit: EndLimit,
    ):
        # Need to Test this for byte ordering doc's arent clear
        return self._write_registers(
            HoldingRegisters.SET_HOME_PARAM,
            [(home_trigger << 1) | home_direction, home_speed, home_end_limit],
        )

    def set_hold_current(self, value: int):
        # Need to Test this for byte ordering doc's arent clear
        return self._write_register(HoldingRegisters.SET_HOLD_CURRENT, value)

    def set_subdivision(self, value: int):
        return self._write_register(HoldingRegisters.SET_SUBDIVISION, value)

    def set_enable_active_level(self, value: EnableActiveLevel):
        return self._write_register(HoldingRegisters.SET_EN_LOGIC, value)

    def set__motor_dir(self, value: MotorRotation):
        return self._write_register(HoldingRegisters.SET_DIR, value)

    def set_shaft_locked(self, value: Enabled):
        return self._write_register(HoldingRegisters.SET_ROTOR_LOCK_STATUS, value)

    def set_interpolation(self, value: Enabled):
        return self._write_register(HoldingRegisters.SET_INTERPOLATION, value)

    def set_baudrate(self, value: Baudrate):
        return self._write_register(HoldingRegisters.SET_BAUDRATE, value)

    def set_slave_address(self, value: int):
        return self._write_register(HoldingRegisters.SET_SLAVE_ADDRESS, value)

    def set_axis_to_zero(self):
        return self._write_register(HoldingRegisters.SET_AXIS_TO_ZERO, 1)

    def go_home(self):
        return self._write_register(HoldingRegisters.GO_HOME, 1)

    def stop(self):
        return self._write_register(HoldingRegisters.ESTOP, 1)


#   """
#   def get_encoder_value_carry(self) -> int:
#      return self.client.read_input_registers(0x30, 3, slave=self.address)
#
#   def get_motor_speed(self) -> int:
#       return self.client.read_input_registers(0x32, 1, slave=self.address)
#
#   def get_pulses(self) -> int:
#       return self.client.read_input_registers(0x33, 2, slave=self.address)
#
#   def get_io_port(self) -> int:
#       return self.client.read_input_registers(0x34, 1, slave=self.address)
#
#   def get_error_angle(self) -> int:
#       return self.client.read_input_registers(0x39, 2, slave=self.address)
#
#   def get_go_to_zero_status(self) -> int:
#       return self.client.read_input_registers(0x3B, 1, slave=self.address)
#
#   def set_sub_division(self, value: int) -> int:
#     return self.client.write_register(0x84, value, slave=self.address)
#
#   """
