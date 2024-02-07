from typing import List, Union
import cv2
import numpy as np
import base64
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def process_image(file_content: bytes):
    # Decode the base64 content
    image_array = np.frombuffer(file_content, np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # Resize the image (adjust dimensions as needed)
    resized_img = cv2.resize(img, (400, 300))

    gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Hough Line Transform
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100,
                            minLineLength=100, maxLineGap=10)

    min_distance = float('inf')
    nearest_line = None

# Calculate the center of the image
    height, width = resized_img.shape[:2]
    center_x = width // 2
    center_y = height // 2 + 100

    # Iterate through the detected lines
    for line in lines:
        x1, y1, x2, y2 = line[0]

        # Calculate the distance from the center to the line
        distance_to_center = cv2.pointPolygonTest(
            np.array([(x1, y1), (x2, y2)], np.int32), (center_x, center_y), True)

        # Update the nearest line if the current line is closer to the center
        if abs(distance_to_center) < min_distance:
            min_distance = abs(distance_to_center)
            nearest_line = line

        # Draw each line in green
        cv2.line(resized_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Draw horizontal line representing the ground level from the starting point of the blue line
    cv2.line(resized_img, (0, center_y), (width, center_y), (0, 0, 255), 2)

    # Draw a vertical red line from the center point
    cv2.line(resized_img, (center_x, 0), (center_x, height), (0, 0, 255), 2)

    # Draw the nearest line in blue
    if nearest_line is not None:
        x1, y1, x2, y2 = nearest_line[0]
        cv2.line(resized_img, (x1, y1), (x2, y2), (255, 0, 0), 2)

        # Calculate the angle clockwise from the red line to the blue line===============================3
        # angle_clockwise = np.arctan2(center_y - y2, x2 - center_x) * (180 / np.pi)

        # # Display the angle on the image
        # cv2.putText(resized_img, f'Angle: {angle_clockwise:.2f} degrees', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        # Calculate the intersection point of the blue line with the ground line
        if y2 - y1 != 0:
            intersection_x = int((center_y - y1) * (x2 - x1) / (y2 - y1) + x1)
        else:
            # Handle the case when y2 - y1 is zero (division by zero)
            intersection_x = center_x  # Set a default value or handle it accordingly
            print("Warning: Division by zero. Setting intersection_x to default value.")

        intersection_y = center_y

        # Draw the extended blue line until it intersects with the ground line
        cv2.line(resized_img, (x1, y1),
                 (intersection_x, intersection_y), (255, 0, 0), 2)

        # Draw a point at the center of the image
        cv2.circle(resized_img, (center_x, center_y), 5, (255, 0, 0), -1)

        # Draw yellow circle around the intersection point
        circle_radius = 20
        cv2.circle(resized_img, (intersection_x, intersection_y),
                   circle_radius, (0, 255, 255), 2)

        # Draw a yellow circle from the red line until the blue line
        # cv2.ellipse(resized_img, (intersection_x, intersection_y), (int(min_distance), int(min_distance)), 0, angle_clockwise, 0, (0, 255, 255), 2)

        # Determine if the yellow circle is to the right or left of the vertical red line
        if intersection_x > center_x:
            position_text = 'Right'
        else:
            position_text = 'Left'

        # Display the position information
        # cv2.putText(resized_img, f'Position: {position_text}', (
        #     10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Calculate the angle between the blue line and the horizontal reference line
        angle_blue = np.arctan2(y2 - y1, x2 - x1) * (180 / np.pi)
        if intersection_x > center_x:
            angle_blue = 180 - \
                np.abs(np.arctan2(y2 - y1, x2 - x1) * (180 / np.pi))
            # Draw a green circle at the end of the blue line
            green_circle_radius = 20
            cv2.circle(resized_img, (x2, y2),
                       green_circle_radius, (0, 255, 0), 2)
            if y2 < center_y:
                position_green_text = 'Above'
            else:
                position_green_text = 'Below'

        else:
            # Draw a green circle at the end of the blue line
            green_circle_radius = 20
            cv2.circle(resized_img, (x1, y1),
                       green_circle_radius, (0, 255, 0), 2)
            # Check the position of the green circle relative to the horizontal red line
            if y1 < center_y:
                position_green_text = 'Above'
            else:
                position_green_text = 'Below'

        quadrant_text = 'Not Defined'
        # Determine the quadrant based on the positions of the yellow and green circles
        if intersection_x > center_x:
            if intersection_x-center_x < int(x2)-center_x and intersection_y-center_y >= int(y2)-center_y:
                quadrant_text = 'Quadrant 1'
            elif intersection_x-center_x < int(x2)-center_x and intersection_y-center_y < int(y2)-center_y:
                quadrant_text = 'Quadrant 4'
                angle_blue = 270 - \
                    np.abs(np.arctan2(y2 - y1, x2 - x1) * (180 / np.pi))
        elif intersection_x < center_x:
            if intersection_x-center_x >= int(x1)-center_x and intersection_y-center_y >= int(y1)-center_y:
                quadrant_text = 'Quadrant 2'
            elif intersection_x-center_x >= int(x1)-center_x and intersection_y-center_y < int(y1)-center_y:
                quadrant_text = 'Quadrant 3'
        if quadrant_text == 'Not Defined':
            if intersection_x >= center_x and intersection_y < int(y2):
                quadrant_text = 'Quadrant 3'
                angle_blue = np.arctan2(y2 - y1, x2 - x1) * (180 / np.pi)
            elif intersection_x >= center_x and intersection_y >= int(y2):
                quadrant_text = 'Quadrant 2'
                angle_blue = np.arctan2(y2 - y1, x2 - x1) * (180 / np.pi)
            elif intersection_x < center_x and intersection_y >= int(y1):
                quadrant_text = 'Quadrant 1'
                angle_blue = 180 - \
                    np.abs(np.arctan2(y2 - y1, x2 - x1) * (180 / np.pi))
            elif intersection_x < center_x and intersection_y < int(y1):
                quadrant_text = 'Quadrant 4'
                angle_blue = 270 - \
                    np.abs(np.arctan2(y2 - y1, x2 - x1) * (180 / np.pi))

        # Display the quadrant information
        # cv2.putText(resized_img, f'Quadrant: {quadrant_text}', (
        #     10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2, cv2.LINE_AA)

        cv2.putText(resized_img, f'Angle Blue: {angle_blue:.2f} degrees', (
            10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Calculate the angle between the red line and the horizontal reference line as the complementary angle to the blue angle==================================2
        # angle_red = 180 - np.abs(angle_blue)
        # cv2.putText(resized_img, f'Angle Red: {angle_red:.2f} degrees', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

        # # Display the position of the green circle relative to the horizontal red line ==========================================================================1
        # cv2.putText(resized_img, f'Green Circle Position: {position_green_text}', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # print("intersection_x 1.", str(intersection_x-center_x) +
        #       " x1 2.", str(x1-center_x) + " x2 3.", str(x2-center_x))
        # print("intersection_y 3.", str(intersection_y-center_y) +
        #       " y1 4.", str(y1-center_y) + " y2 3.", str(y2-center_y))
        # print('angle_blue', angle_blue)
        # print('position_text', position_text)
        # print('position_text', quadrant_text)

    # Convert the processed image to base64
    _, img_encoded = cv2.imencode('.png', resized_img)
    img_base64 = base64.b64encode(img_encoded).decode("utf-8")
    data = {
        "angle_blue": angle_blue,
        "position_text": position_text,
        "quadrant_text": quadrant_text,
        "processed_image": img_base64
    }

    return {"data": data}


@app.post("/process_image/")
async def process_image_endpoint(file: UploadFile = File(...)):
    # Read the content of the file
    file_content = await file.read()

    # Process the image
    result = process_image(file_content)

    return result
