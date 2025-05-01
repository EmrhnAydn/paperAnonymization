# Project Name

## Overview

This project is designed to [briefly describe the purpose of the project, e.g., "anonymize documents and manage user interactions through a web interface"]. It consists of a backend and a frontend component, each serving distinct roles in the overall functionality. This project determines the area of ​​expertise of the article with NLP and ensures that it is directed to the appropriate referee. It encrypts the information of the article authors with AES and detects and blurs the images of the authors with Poppler. In this way, anonymization is ensured in the articles sent to the referee.

## Project Structure

- **anonymApp/**: Main application directory.
  - **backend/**: Contains the server-side logic and database interactions.
    - `app.py`: Main application script for backend operations.
    - `models.py`: Defines the data models used in the application.
    - `pdfBluring.py`: Handles PDF blurring functionalities.
    - `anonymizer.py`: Contains logic for anonymizing documents.
    - `expertSelector.py`: Logic for selecting experts based on criteria.
  - **frontend/**: Contains the client-side code and templates.
    - **templates/**: HTML templates for rendering web pages.
      - `yonetici_paneli.html`: Admin panel interface.
      - `hakem_paneli.html`: Reviewer panel interface.
      - `show_result.html`: Displays results to the user.
      - `makale_durum_sorgulama.html`: Article status inquiry page.
      - `revize_yukle.html`: Page for uploading revisions.
      - `chat.html`: Chat interface.
      - `base.html`: Base template for other HTML files.
      - `makale_yukleme.html`: Article upload page.
      - `index.html`: Main landing page.

## Installation

1. Clone the repository:
   ```bash
   git clone [repository URL]
   ```
2. Navigate to the project directory:
   ```bash
   cd anonymApp
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the backend server:
   ```bash
   python backend/app.py
   ```
2. Access the frontend by opening `index.html` in a web browser or by navigating to the appropriate URL if hosted on a server.

## Features

- **Document Anonymization**: Automatically anonymizes sensitive information in documents.
- **User Management**: Admin and reviewer panels for managing user interactions.
- **Real-time Chat**: Integrated chat functionality for user communication.
- **Article Management**: Upload, review, and track the status of articles.

