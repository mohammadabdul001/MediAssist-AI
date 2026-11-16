# MediAssist AI

MediAssist AI is an AI-powered, web-based healthcare assistance platform
designed to help users understand reported symptoms, manage health
information, access healthcare services, and receive timely reminders.
It is intended to support patients and healthcare professionals with
accessible, personalized health information.

> **Medical disclaimer:** MediAssist AI is an informational and
> decision-support tool. It does not replace a qualified healthcare
> professional, medical diagnosis, or emergency medical care. Users
> should seek professional help for medical concerns and contact local
> emergency services in an emergency.

## Key Features

-   **AI symptom analysis:** Accepts user-reported symptoms and provides
    preliminary condition suggestions, risk-oriented information, and
    guidance.
-   **Health record management:** Centralizes patient profiles, medical
    history, lab reports, and consultation records.
-   **Personalized health recommendations:** Provides lifestyle
    suggestions related to diet, exercise, and medication adherence.
-   **AI chatbot assistance:** Supports health-related questions and
    guidance through conversational interaction.
-   **Appointment scheduling:** Supports booking, rescheduling, and
    managing appointments with healthcare providers.
-   **Telemedicine:** Designed to support remote consultations using
    WebRTC or a compatible video-call service.
-   **Medication tracker:** Tracks medicines and provides dose and
    refill reminders.
-   **Lab test management:** Supports lab test requests, report uploads,
    and result notifications.
-   **Health analytics:** Presents health trends and insights based on
    available user data.
-   **Emergency SOS:** Supports emergency alerts with location and
    relevant health information shared with configured contacts.
-   **Role-based access:** Defines access for patients, doctors, lab
    technicians, pharmacy staff, and administrators.
-   **Accessibility and multilingual support:** Aims to provide a
    responsive, accessible interface for users with different needs.

## Technology Stack

The project report describes the following technologies:

  -----------------------------------------------------------------------
  Layer                               Technology
  ----------------------------------- -----------------------------------
  Frontend                            HTML, CSS, JavaScript

  Backend                             Python 3.8, Flask

  Database                            MongoDB

  AI / Machine Learning               TensorFlow 2.0 and NLP libraries

  Authentication                      JWT-based authentication and
                                      role-based access control

  Telemedicine                        WebRTC / compatible video-call API

  Healthcare data exchange            HL7 FHIR (planned/integration
                                      context)
  -----------------------------------------------------------------------

The report also discusses cloud infrastructure and GPU-enabled AI
inference. The exact deployment provider and environment-specific
configuration should be added for the repository where applicable.

## System Overview

At a high level, the application follows this workflow:

1.  A user registers or signs in and accesses the features permitted by
    their role.
2.  The frontend collects symptoms or other health-related information.
3.  Requests are sent to the Python/Flask backend.
4.  The backend coordinates application logic, database operations, and
    AI inference through TensorFlow.
5.  Relevant records are stored in MongoDB.
6.  Results, reminders, notifications, and other responses are returned
    to the user interface.

The report identifies `/api/symptom-analysis` as the symptom-analysis
endpoint.

## User Roles

-   **Patient:** Enters symptoms, manages personal health records and
    medicines, books appointments, and can trigger SOS alerts.
-   **Doctor / Healthcare Provider:** Reviews patient information with
    appropriate permission, manages consultations, and updates clinical
    notes.
-   **Lab Technician:** Processes lab requests and uploads test results.
-   **Pharmacy Staff:** Verifies prescriptions and manages medicine
    availability and refill information.
-   **Administrator:** Manages user roles, access, system activity, and
    maintenance.

## Security and Responsible Use

The project report describes security and privacy measures including:

-   Role-Based Access Control (RBAC).
-   JWT-based authentication.
-   Encryption of sensitive data (AES-256 is specified in the report).
-   Secure communication (TLS 1.3 is specified in the report).
-   Audit logging and data-minimization practices.
-   User consent and controlled sharing of health information.
-   Clinical disclaimers and human review for high-risk cases.

**Deployment note:** Do not use real patient information in development
or public demonstrations. Before handling real health data,
independently verify the implementation, infrastructure, legal
requirements, consent flows, and applicable healthcare regulations. A
statement in a project report is not, by itself, proof of regulatory
compliance or clinical validation.

## Getting Started

The report specifies the technology stack, but does not provide a
complete repository-specific installation procedure, dependency
lockfile, environment-variable list, or deployment configuration. The
commands below are a general starting point; adjust them to match the
actual source code in this repository.

### Prerequisites

-   Python 3.8 (as specified in the report)
-   MongoDB
-   pip
-   A modern web browser

### Setup

1.  Clone the repository:

    ``` bash
    git clone <your-repository-url>
    cd <your-repository-folder>
    ```

2.  Create and activate a virtual environment:

    ``` bash
    python -m venv venv
    ```

    Windows:

    ``` bash
    venv\Scripts\activate
    ```

    macOS / Linux:

    ``` bash
    source venv/bin/activate
    ```

3.  Install the project dependencies if a `requirements.txt` file is
    present:

    ``` bash
    pip install -r requirements.txt
    ```

4.  Configure MongoDB and any required environment variables. Use the
    variable names expected by your application code. Do not commit
    credentials, API keys, tokens, or production connection strings.

5.  Start the backend using the entry point configured in your
    repository. For a Flask application whose entry point is `app.py`, a
    typical development command is:

    ``` bash
    flask --app app run --debug
    ```

6.  Open the frontend using the development or serving procedure
    configured for the frontend files.

> **Important:** The application entry point, frontend start command,
> dependency list, and required environment variables must be confirmed
> from the actual repository. The example commands above are not
> guaranteed to run unchanged.

## Testing

The report describes testing across the following areas:

-   Unit testing of symptom analysis, authentication, and medication
    tracking.
-   Functional testing of appointments, health-record operations,
    telemedicine, and SOS alerts.
-   Security testing of role permissions and protected health
    information.
-   Performance testing of AI inference and database operations.
-   Usability and accessibility evaluation.

Run the test suite provided in the repository. Add the exact test
command here once the project test configuration is known.

## Future Enhancements

The report identifies these possible future improvements:

-   Medical image processing for image-based symptom input.
-   Multimodal analysis combining text, voice, images, and wearable
    vital signs.
-   Predictive health-risk modelling for chronic conditions.
-   Deeper integration with smartwatches and biosensors.
-   Expanded telehealth referrals and home-healthcare services.
-   Dedicated mobile applications and offline first-aid guidance.
-   Wider regional language and regulatory support.
-   Decentralized health records and privacy-preserving technologies.

## Project Information

**Project:** MediAssist AI\
**Type:** Academic project -- web-based AI healthcare assistant\
**Institution:** Parul University\
**Project guide:** Assistant Prof. Aseem Gupta\
**Academic year:** 2025--2026

## Contributors

-   Farheensayed M Nalband
-   K. Naveen Kumar
-   G. T. Pavan Sai
-   Md. Abdul Muthallib

## Contributing

Contributions and suggestions are welcome. For changes:

1.  Fork the repository.
2.  Create a feature branch.
3.  Make and test your changes.
4.  Open a pull request describing the change.

Do not include real patient data, secrets, or personally identifiable
health information in commits or issue reports.

## License

No license is specified in the project report. Add a `LICENSE` file and
update this section before distributing or reusing the project.
