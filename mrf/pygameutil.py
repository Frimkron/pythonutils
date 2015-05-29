import pygame
import pygame.joystick
import math

TAU = math.pi*2


class XBox360Pad(object):

    AXIS_LSTICK_X = 0
    AXIS_LSTICK_Y = 1
    AXIS_RSTICK_X = 3
    AXIS_RSTICK_Y = 4
    AXIS_LEFT_TRIGGER = 2
    AXIS_RIGHT_TRIGGER = 5
    
    BUTTON_LEFT_BUMPER = 4
    BUTTON_RIGHT_BUMPER = 5
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_X = 2
    BUTTON_Y = 3
    BUTTON_START = 7
    BUTTON_BACK = 6
    BUTTON_CENTRE = 8
    BUTTON_LEFT_STICK = 9
    BUTTON_RIGHT_STICK = 10

    HAT_DPAD = 0
    
    DEAD_ZONE = 0.2

    @staticmethod
    def find_all():
        pads = []
        for jid in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(jid)
            joy.init()
            if "360" not in joy.get_name(): continue
            if joy.get_numaxes() != 6: continue
            if joy.get_numballs() != 0: continue
            if joy.get_numbuttons() != 11: continue
            if joy.get_numhats() != 1: continue
            pads.append(XBox360Pad(joy))
        return pads

    joystick = None
    init_triggers = [False,False]

    def __init__(self,joystick):
        self.joystick = joystick
        self.init_triggers = [False,False]

    def get_left_stick(self):
        return (
            self._apply_dead_zone(self.joystick.get_axis(self.AXIS_LSTICK_X)),
            self._apply_dead_zone(self.joystick.get_axis(self.AXIS_LSTICK_Y)) )

    def get_left_stick_click(self):
        return self.joystick.get_button(self.BUTTON_LEFT_STICK)

    def get_right_stick(self):
        return (
            self._apply_dead_zone(self.joystick.get_axis(self.AXIS_RSTICK_X)),
            self._apply_dead_zone(self.joystick.get_axis(self.AXIS_RSTICK_Y)) )
    
    def get_right_stick_click(self):
        return self.joystick.get_button(self.BUTTON_RIGHT_STICK)
    
    def get_left_trigger(self):
        axval = self.joystick.get_axis(self.AXIS_LEFT_TRIGGER)
        if not self.init_triggers[0]:
            if axval==0: return 0.0
            self.init_triggers[0] = True        
        return (axval+1.0) / 2.0
    
    def get_right_trigger(self):
        axval = self.joystick.get_axis(self.AXIS_RIGHT_TRIGGER)
        if not self.init_triggers[1]:
            if axval==0: return 0.0
            self.init_triggers[1] = True
        return (axval+1.0) / 2.0
    
    def get_left_bumper(self):
        return self.joystick.get_button(self.BUTTON_LEFT_BUMPER)
    
    def get_right_bumper(self):
        return self.joystick.get_button(self.BUTTON_RIGHT_BUMPER)
    
    def get_a_button(self):
        return self.joystick.get_button(self.BUTTON_A)
        
    def get_b_button(self):
        return self.joystick.get_button(self.BUTTON_B)
        
    def get_x_button(self):
        return self.joystick.get_button(self.BUTTON_X)
        
    def get_y_button(self):
        return self.joystick.get_button(self.BUTTON_Y)
    
    def get_start_button(self):
        return self.joystick.get_button(self.BUTTON_START)
        
    def get_back_button(self):
        return self.joystick.get_button(self.BUTTON_BACK)
    
    def get_centre_button(self):
        return self.joystick.get_button(self.BUTTON_CENTRE)
    
    def get_dpad(self):
        dpad = self.joystick.get_hat(self.HAT_DPAD)
        return ( dpad[0], dpad[1]*-1 )

    def to_ascii_art(self):
        data = [" "]*41
        ls = self.get_left_bumper()
        for i in (0,1,2,3): data[i] = "." if ls else "_"
        rs = self.get_right_bumper()
        for i in (4,5,6,7): data[i] = "." if rs else "_"
        data[18] = "O" if self.get_back_button() else "o"
        data[19] = "X" if self.get_centre_button() else "x"
        data[20] = "O" if self.get_start_button() else "o"
        data[12] = "Y" if self.get_y_button() else "y"
        data[21] = "X" if self.get_x_button() else "x"
        data[22] = "B" if self.get_b_button() else "b"
        data[25] = "A" if self.get_a_button() else "a"
        lt = self.get_left_trigger()
        for idx,i in enumerate((27,24,14,8)): data[i] = "#" if lt > idx*0.25 else " "
        rt = self.get_right_trigger()
        for idx,i in enumerate((34,26,23,13)): data[i] = "#" if rt > idx*0.25 else " "
        data[9],data[10],data[11],data[15],data[16],data[17] = self._directional_to_ascii(self.get_left_stick())
        data[31],data[32],data[33],data[38],data[39],data[40] = self._directional_to_ascii(self.get_right_stick())
        data[28],data[29],data[30],data[35],data[36],data[37] = self._directional_to_ascii(self.get_dpad())
        aart = """\
                     ****           ****
                   .------_________------.
            |*|   / /***`            (*)  `   |*|
            |*|  /  `***/  * (*) * (*) (*) `  |*|
            |*| |                    (*)    | |*|
            |*| |       /***`   /***`       | |*|
                |       `***/   `***/       |
                |    ...-------------...    |
                '---'                   '---'
        """.replace("\t","").replace("`","\\").replace("*","%s") % tuple(data)
        return aart
    
    def _directional_to_ascii(self,axes):
        retval = [" "]*6
        if axes[0]==0 and axes[1]==0:
            ang = None
        else:
            ang = math.atan2(axes[1],axes[0])
        retval[0] = "_" if ang is not None and (ang < TAU/16*-7 or ang > TAU/16*7) else (
            "\\" if ang is not None and TAU/16*-7 <= ang < TAU/16*-5 else " ")
        retval[1] = "." if ang is None else ("|" if TAU/16*-5 <= ang < TAU/16*-3 else " ")
        retval[2] = "_" if ang is not None and TAU/16*-1 <= ang <= TAU/16*1 else (
            "/" if ang is not None and TAU/16*-3 <= ang < TAU/16*-1 else " ")
        retval[3] = "/" if ang is not None and TAU/16*5 <= ang < TAU/16*7 else " "
        retval[4] = "|" if ang is not None and TAU/16*3 <= ang < TAU/16*5 else " "
        retval[5] = "\\" if ang is not None and TAU/16*1 <= ang < TAU/16*3 else " "
        return tuple(retval)
    
    def _apply_dead_zone(self,val):
        if abs(val) < self.DEAD_ZONE: return 0
        dir = val / abs(val) if val != 0 else 1
        return (val-self.DEAD_ZONE*dir) / (1-self.DEAD_ZONE)

    
