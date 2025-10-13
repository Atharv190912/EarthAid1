# EarthAid - A Youth-Led Environmental Action Platform

## Overview

EarthAid is a Streamlit application designed to empower individuals, especially youth, to take action on environmental issues. It allows users to:

* Report environmental concerns in their local areas.
* Discover and participate in community-driven environmental initiatives.
* View a live map of reported issues and initiatives.
* Earn "LifePoints" for their contributions and compete on a leaderboard.
* Potentially receive a "Certificate of Impact" for active participation.

This platform is built with the vision of fostering a collaborative and impactful approach to environmental protection.

## Getting Started

These instructions will guide you on how to run the EarthAid application on your local machine.

### Prerequisites

Make sure you have the following installed on your system:

* **Python 3.6+**: You can download it from [python.org](https://www.python.org/downloads/).
* **pip**: Python package installer, usually included with Python installations.

### Installation

1.  **Clone the repository** (if you have the code in a Git repository). If you have the `your_script_name.py` file directly, you can skip this step.

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install the required Python libraries.** Navigate to the directory containing the `your_script_name.py` file (and this `README.md` file) in your terminal and run:

    ```bash
    pip install streamlit pandas pydeck
    ```

    This command will install the necessary libraries:
    * `streamlit`: For creating the web application.
    * `pandas`: For data manipulation (reading and writing CSV files).
    * `pydeck`: For creating interactive maps.

### Running the Application

1.  **Open your terminal or command prompt.**
2.  **Navigate to the directory** where you saved the `your_script_name.py` file.
3.  **Run the Streamlit application** using the following command:

    ```bash
    streamlit run your_script_name.py
    ```

    Replace `your_script_name.py` with the actual name of your Python script if it's different.

4.  **The application will automatically open in your web browser.** If it doesn't, you should see a local URL in your terminal (usually something like `http://localhost:8501`) that you can open in your browser.

## How to Use EarthAid

Once the application is running in your browser, you can navigate through the different tabs:

* **Home:** Provides an overview of the EarthAid platform, its mission, creator, and key features.
* **Report Environment:** Allows you to submit reports about environmental issues you observe, including a description, location (by city), and your username. Reporting earns you LifePoints.
* **Live Earth Map:** Displays a global map showing the locations of submitted environmental reports.
* **Initiatives:** Features two sub-tabs:
    * **Submit Initiative:** Enables you to share your own environmental initiatives with the community. Submitting an initiative also earns you LifePoints.
    * **View Initiatives:** Lists the initiatives submitted by other users.
* **Profile:** Lets you check your current LifePoints by entering your username.
* **Leaderboard:** Shows the ranking of users based on their accumulated LifePoints.

## Data Storage

EarthAid uses simple CSV files to store the application data:

* `reports.csv`: Contains details of the environmental reports submitted by users.
* `initiatives.csv`: Stores information about the environmental initiatives shared by users.
* `points.csv`: Tracks the LifePoints earned by each user.

These files will be created automatically in the same directory as the script if they don't exist.