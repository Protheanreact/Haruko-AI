import pc_control
import time

print("Testing Notepad launch...")
result = pc_control.launch_app("notepad")
print(result)

print("Testing Calc launch...")
result = pc_control.launch_app("rechner")
print(result)
