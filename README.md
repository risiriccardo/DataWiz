# DataWiz
This project is designed to run with Python 3.11 and uses Streamlit for the front end

## Prerequisites

- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html): Make sure you have Conda installed!
- Python 3.11: Ensure you have Python 3.11 compatible with Conda.

## Setup Instructions

Follow these steps to create a Conda environment, install the necessary dependencies, and run the Streamlit application.

1. Clone this repository to your local machine:

```bash
git clone https://github.com/risiriccardo/DataWiz.git
cd DataWiz
```

2. Create an environment and install the dependencies:
```bash
conda create -n DataWiz python=3.11
conda activate DataWiz
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run main.py
```
