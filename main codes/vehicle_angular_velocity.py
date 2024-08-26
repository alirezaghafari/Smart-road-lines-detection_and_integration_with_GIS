import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# The purpose of this code is to calculate and store the angular velocity (yaw_derivative) from the orientation data.
# The yaw_derivative helps in identifying and filtering out lines with low slopes that are considered outliers.
# While filtering, we ensure that lines with low slopes are not removed if the vehicle is turning or on a curved road, as lines on curves naturally have lower slopes.

def yaw_derivative(file_path: str, output_file_path: str):
    df = pd.read_csv(file_path)

    # Extract the columns 'seconds_elapsed' and 'yaw'
    extracted_columns = df[['seconds_elapsed', 'yaw']].copy()

    # Adjust yaw values to handle wrapping from +π to -π
    yaw_values = extracted_columns['yaw'].values
    for i in range(1, len(yaw_values)):
        if yaw_values[i] - yaw_values[i - 1] > np.pi:
            yaw_values[i] -= 2 * np.pi
        elif yaw_values[i - 1] - yaw_values[i] > np.pi:
            yaw_values[i] += 2 * np.pi
    extracted_columns['yaw'] = yaw_values

    # Compute the derivative of yaw with respect to seconds_elapsed
    extracted_columns['yaw_derivative'] = np.gradient(extracted_columns['yaw'], extracted_columns['seconds_elapsed'])

    # Filter out derivatives with absolute values greater than 10
    extracted_columns.loc[np.abs(extracted_columns['yaw_derivative']) > 10, 'yaw_derivative'] = 0

    # Set the start time
    start_time_str = '09:23:13.364' # You need to change this based on the start time of your recorded video. The Timestamp Camera app records the time of the first frame in milliseconds.
    start_time = pd.to_datetime(start_time_str, format='%H:%M:%S.%f')

    # Convert seconds_elapsed to actual time and extract hours, minutes, and seconds
    extracted_columns['exact_time'] = (start_time + pd.to_timedelta(extracted_columns['seconds_elapsed'], unit='s')).dt.strftime('%H:%M:%S')

    # Select the relevant columns
    final_columns = extracted_columns[['exact_time', 'seconds_elapsed', 'yaw', 'yaw_derivative']]

    # Save to a CSV file
    final_columns.to_csv(output_file_path, index=False)
    print("Data has been successfully saved.")

    return final_columns

def plot_data(data: pd.DataFrame):
    plt.figure(figsize=(14, 8))

    # Plot yaw
    plt.subplot(2, 1, 1)
    plt.plot(data['seconds_elapsed'], data['yaw'], label='Yaw', color='blue')
    plt.xlabel('Seconds Elapsed')
    plt.ylabel('Yaw')
    plt.title('Yaw vs. Seconds Elapsed')
    plt.legend()
    plt.grid(True)

    # Plot yaw derivative
    plt.subplot(2, 1, 2)
    plt.plot(data['seconds_elapsed'], data['yaw_derivative'], label='Yaw Derivative', color='red')
    plt.xlabel('Seconds Elapsed')
    plt.ylabel('Yaw Derivative')
    plt.title('Yaw Derivative vs. Seconds Elapsed')
    plt.legend()
    plt.grid(True)

    # Display the plots
    plt.tight_layout()
    plt.show()

file_path = 'IMU_data/Orientation.csv'
output_file_path = 'IMU_data/Angular_Velocity.csv'

# Extract data and save it
data = yaw_derivative(file_path, output_file_path)

# plot data as needed
plot_data(data)
