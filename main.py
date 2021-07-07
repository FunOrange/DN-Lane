import PIL.ImageGrab
import numpy
import cv2
import keyboard
import time
import json
import traceback
import os
from datetime import datetime
from ahk import AHK
ahk = AHK()

# --- run as admin ---
import ctypes, sys
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
# --------------------

# how often to scan the screen
tick_interval_ms = 300
# confidence requirement for image matching
confidence_req = 98.5

always_click_these_images = [
  '1280x720/tap_to_continue.png',
  '1280x720/crap1.png',
  '1280x720/crap2.png',
  "1280x720/touch_to_continue.png",
  "1280x720/confirm.png",
  "1280x720/confirm2.png",
  "1280x720/confirm3.png",
  "1280x720/continue.png",
  "1280x720/rare.png",
  "1280x720/elite.png",
  "1280x720/super_rare.png",
  "1280x720/autosearch_off.png",
]

press_escape_on_these_images = [
  "1280x720/new.png",
  "1280x720/got_it.png",
  "1280x720/got_it2.png",
  "1280x720/defeat.png"
]

# returns x, y coordinates of button, or None if image is not found
def find_image_on_screen(img_path):
  screen_rgb = numpy.array(PIL.ImageGrab.grab())
  screen = cv2.cvtColor(screen_rgb, cv2.COLOR_RGB2BGR)
  button = cv2.imread(img_path)

  # match
  result = cv2.matchTemplate(button, screen, cv2.TM_SQDIFF_NORMED)
  min_error, _, min_error_coords, _ = cv2.minMaxLoc(result)
  confidence = (1 - min_error) * 100
  if confidence < confidence_req:
    # print(f'No confidence ({confidence:.2f}%)')
    return None
  # print(f'Found {img_path} with confidence: {confidence:.2f}%')

  # Extract the coordinates oggf our best match
  match_x, match_y = min_error_coords
  height, width = button.shape[:2]

  cv2.rectangle(screen, (match_x,match_y),(match_x+width,match_y+height),(0,0,255),2)
  cv2.putText(screen, f'{confidence:.2f}%', (match_x, match_y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
  dt = datetime.now().strftime('%Y_%m_%d-%I_%M_%S')
  filename = f'history/{dt}-{os.path.splitext(os.path.basename(img_path))[0]}.jpg'
  cv2.imwrite(filename, screen) 
  return (int(match_x + width/2), int(match_y + height/2))

# same structure as json file but with extra state variables
class AutoTask:
  def __init__(self, task):
    self.name = task['name']
    self.image_sequence = task['image_sequence']
    self.progress = 0

def main():
  # 
  lists = [f for f in os.listdir() if f.endswith('_list.json')]
  i = 0
  for file in lists:
    print(f'{i} - {file}')
    i += 1
  if len(lists) > 1:
    index = int(input('Choose file: '))
  else:
      index = 0
  selected_exec_list = lists[index]

  current_task_number = 0
  # load script
  tasks = []
  with open(selected_exec_list) as f:
    exec_list = json.load(f)
  with open("tasks.json") as f:
    task_list = json.load(f)
    for e in exec_list:
      task = next(t for t in task_list if t['name'] == e)
      tasks.append(AutoTask(task))
  current_task = tasks[0]

  ms = 0
  while current_task_number < len(tasks):
    # this is checked very frequently
    if keyboard.is_pressed('q'):
      print('Quitting...')
      sys.exit(0)

    # main logic
    # this is run less frequently
    if ms % tick_interval_ms == 0:

      # get current image
      current_image = current_task.image_sequence[current_task.progress]
      print(f'{current_task_number+1}/{len(tasks)} {current_task.name}: looking for {current_image} ({current_task.progress+1}/{len(current_task.image_sequence)})...')

      # look for button to click
      coords = find_image_on_screen(current_image)
      if coords is not None: 
        # click the button
        x, y = coords
        ahk.click(x, y)
        # move on to the next button
        current_task.progress += 1 

        while current_task.progress == len(current_task.image_sequence):
          # move on to the next task
          current_task_number += 1
          current_task.progress = 0
          if current_task_number == len(tasks):
            print("")
            input("Finished!")
            sys.exit(0)
          current_task = tasks[current_task_number]
      else:
        # button not found
        # try to look for always_click_these_images
        for always_img in always_click_these_images:
          coords = find_image_on_screen(always_img)
          if coords is not None: 
            print(f'Clicking {always_img}')
            x, y = coords
            ahk.click(x, y)
        for esc_img in press_escape_on_these_images:
          coords = find_image_on_screen(esc_img)
          if coords is not None: 
            print(f'Pressing escape on {esc_img}')
            ahk.key_press('Escape')

    time.sleep(0.001) # 1 ms
    ms += 1

  print("")
  input("Finished!")

if __name__ == "__main__":
  if is_admin():
    try:
      main()
    except Exception as e:
      traceback.print_exc()
      input('error lol')
  else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
