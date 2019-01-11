#!/usr/bin/env python

import math
import rospy
import numpy
from control.msg import drive_param
from sensor_msgs.msg import LaserScan

targetdist = 0.55
sidetargetdist = 0.5

max_fwd_speed = 40
min_fwd_speed = 25
max_rev_speed = -30
min_rev_speed = -25
max_left_angle = -60
max_right_angle = 60

kp = [25, 30]
ki = [0, 0]
kd = [0.09, 0.25]

prev_error = 0
sum_error = 0
prev_angle_error = 0
sum_angle_error = 0

pub = rospy.Publisher('control_drive_parameters', drive_param, queue_size=1)

def offhook():
    msg = drive_param()
    msg.velocity = 0
    msg.angle = 0
    pub.publish(msg)

def getRange(data, theta):
    step = [int(i/data.angle_increment) for i in theta]
    distance = [data.ranges[i] for i in step]
    return distance


def callback(data):

    rospy.on_shutdown(offhook)

    global prev_error
    global sum_error
    global prev_angle_error
    global sum_angle_error

    angle_range = data.angle_max - data.angle_min

    cur_error = 0
    cur_angle_error = 0
    
    if (True): 
        right = 0.4 * angle_range
        forward = 0.5 * angle_range
        left = 0.6 * angle_range
        angles = [forward, left, right]
        
        actualdist = getRange(data, angles)

        cur_error =  actualdist[0] - targetdist
    	cur_angle_error = actualdist[1] - actualdist[2]
        print ('distances: [%s]' % ', '.join(map(str, actualdist)))
	
    else:
        angle1 = 0
        angle2 = 50
        swing = math.radians(angle2 - angle1)
        forward = 0.5 * angle_range
        angles = [forward, angle1, angle2]

        actualdist = getRange(data, angles)
        
        alpha = math.atan2((actualdist[2] * math.cos(swing)) - actualdist[1], actualdist[2] * math.sin(swing))
        AB = actualdist[1] * math.cos(alpha)
        AC = 1
        CD = AB + (AC * math.sin(alpha))
        
        cur_error =  actualdist[0] - targetdist
        cur_angle_error = -1*(CD - sidetargetdist)
        print ('distances: [%s]' % ', '.join(map(str, actualdist)))

    d_time = 1
    d_error = prev_error - cur_error
    sum_error += cur_error * d_time

    p_value = kp[0]*cur_error
    i_value = ki[0]*sum_error
    d_value = kd[0]*(d_error/d_time)

    d_angle_error = prev_angle_error - cur_angle_error
    sum_angle_error += cur_angle_error * d_time

    p_a_value = kp[1]*cur_angle_error
    i_a_value = ki[1]*sum_angle_error
    d_a_value = kd[1]*(d_angle_error/d_time)

    # print ('P: {}, I: {}, D: {}'.format(p_value, i_value, d_value))
    # print ('cur_error: {}, prev_error: {}, sum_error: {}'.format(cur_error, prev_error, sum_error))

    prev_error = cur_error
    prev_angle_error = cur_angle_error

    speed = p_value + i_value + d_value
    speed = max(min(speed, max_fwd_speed), max_rev_speed)

    angle = p_a_value + i_a_value + d_a_value
    angle = min(max(angle, max_left_angle), max_right_angle)

    msg = drive_param()
    msg.velocity = speed
    msg.angle = angle
    print('speed: %f' % speed)
    print('angle: %f' % angle)
    pub.publish(msg)


if __name__ == '__main__':
    print("PID control started")
    rospy.init_node('pid_control', anonymous=True)
    rospy.Subscriber("scan", LaserScan, callback)
    rospy.spin()
