import wpilib

from simple_state_system import *

from phoenix6.hardware import TalonFX
from phoenix6.configs import TalonFXConfiguration

class SubsystemExample(StateSystem):
    def __init__(self):
        # Initialize the state machine
        super().__init__()

        # Create a motor
        self.test_motor = TalonFX(1)
        
        # Apply simple motor configurations
        test_motor_config = TalonFXConfiguration()
        
        test_motor_config.slot0.k_p = 0.1

        self.test_motor.configurator.apply(test_motor_config)

    @state 
    def idle(self):
        self.test_motor.stopMotor()

    @state
    def running(self):
        self.test_motor.set(0.3)

class Robot(wpilib.TimedRobot):
    def robotInit(self):
        self.subsystem = SubsystemExample()
        self.controller = wpilib.XboxController(0)
    
    def teleopPeriodic(self):
        if self.controller.getAButton():
            self.subsystem.set_state("running")
        else:
            self.subsystem.set_state("idle")

if __name__ == "__main__":
    wpilib.run(Robot)