# Routing Agent — Change Delta

## ADDED Requirements

### Requirement: Live Model Status from API
The system SHALL fetch live model status from the Fireworks API /v1/models endpoint.

#### Scenario: Refresh button updates statuses
- **WHEN** the user clicks the Refresh button
- **THEN** the system calls api.fireworks.ai/inference/v1/models
- **AND** updates the Model Pool statuses (UP/SETUP/DOWN) based on the API response

#### Scenario: Serverless model shows UP
- **WHEN** the model is deepseek or glm and present in the API response
- **THEN** the status column shows "[UP]"

#### Scenario: Dedicated deploy shows SETUP
- **WHEN** the model name contains "gemma" and is absent from the API response
- **THEN** the status column shows "[SETUP]"

### Requirement: Interactive Model Pool Table
The system SHALL display the model pool as an interactive sortable table.

#### Scenario: Model pool shows as dataframe
- **WHEN** the sidebar renders
- **THEN** the model pool appears as st.dataframe with sortable columns
- **AND** includes model name, status, pricing, and context length columns

## MODIFIED Requirements

### Requirement: Status Labels
The status labels for models SHALL reflect real API data instead of hardcoded logic, showing UP for serverless models, SETUP for undeployed dedicated models, and DOWN for unreachable local models.

#### Scenario: Gemma 4 shows SETUP
- **WHEN** the model name contains "gemma"
- **THEN** the status column shows "[SETUP]"

#### Scenario: Serverless models show UP
- **WHEN** the model is deepseek or glm
- **THEN** the status column shows "[UP]"

### Requirement: Web Interface
The web interface SHALL provide a Model Pool sidebar with live Refresh button and st.dataframe table display in addition to the core routing functionality.

#### Scenario: Model pool renders as interactive table
- **WHEN** the sidebar renders
- **THEN** the model pool appears as st.dataframe with sortable columns
- **AND** a Refresh button fetches live data from the Fireworks API

#### Scenario: User routes a prompt via web UI
- **WHEN** the user enters a prompt and clicks Route
- **THEN** the system displays the model, accuracy, tokens, cost, and response
