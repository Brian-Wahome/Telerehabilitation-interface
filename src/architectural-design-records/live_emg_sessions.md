# Live emg sensor data flow

This architectural design record(adr) is focused on discussing the potential flows for the
transmission of emg signal data during a therapy session.

## Option 1: WebRTC based architecture

This option involves using webrtc to establish a direct peer to peer (p2p) connection between the emg sensors
and the front-end to stream live emg data. 

The data flow and architecture can be observed in the diagram below.

```mermaid
sequenceDiagram
    participant S as EMG Sensor
    participant SS as STUN/TURN
    participant F as Frontend
    participant B as Backend

    Note over S,B: Initial Setup
    F->>SS: Connect to STUN/TURN server
    S->>SS: Connect to STUN/TURN server
    F->>B: Request new session
    B->>SS: Create session
    
    Note over S,F: WebRTC Setup
    F->>SS: Send offer (SDP)
    SS->>S: Forward offer
    S->>SS: Send answer (SDP)
    SS->>F: Forward answer
    
    Note over S,F: ICE Candidate Exchange
    F->>SS: Send ICE candidates
    SS->>S: Forward ICE candidates
    S->>SS: Send ICE candidates
    SS->>F: Forward ICE candidates
    
    Note over S,F: Direct P2P Connection
    S-->>F: Direct EMG data stream
    
    Note over S,B: Backup Data Path
    S-->>B: Periodic data backup
    
    Note over F,B: Session Management
    F->>B: Session metadata/events
```

### Pros

- Low latency as direct p2p connection is used ,and there is no need for server routing in most cases.
- Reduced load on the server as the server only handles signaling. 
- Built-in security features ensuring data integrity.

### Cons

- More complex to implement
- Overhead complexity as more infrastructure is required.
- Connection recovery is more difficult to achieve
- Webrtc is primarily designed for audio/video transmission which is more complex hence resources may be wasted for emg data transmission.

## Option 2: MQTT over Websockets with TLS

This option uses MQTT over websockets with TLS to stream emg data. 
The architecture diagram can be observed below:

```mermaid
sequenceDiagram
    participant P as Patient UI
    participant T as Therapist UI
    participant B as Backend
    participant M as MQTT Broker
    participant E as EMG Sensors

    T->>B: Request new session
    B->>B: Create session record
    B->>M: Create topics for session
    B->>T: Return session ID & credentials

    P->>B: Join session (with ID)
    B->>B: Validate session
    B->>P: Session details & MQTT credentials

    Note over P,M: TLS Handshake & Connection
    P->>M: Connect (WSS)
    T->>M: Connect (WSS)
    E->>M: Connect (WSS)

    Note over P,M: MQTT Connection
    P->>M: MQTT CONNECT
    M->>P: MQTT CONNACK
    T->>M: MQTT CONNECT
    M->>T: MQTT CONNACK
    E->>M: MQTT CONNECT
    M->>E: MQTT CONNACK

    Note over P,E: Topic Subscriptions
    P->>M: Subscribe (emg/sessions/{id})
    T->>M: Subscribe (emg/sessions/{id})
    E->>M: Subscribe (emg/sessions/{id}/control)

    Note over P,E: Data Streaming
    E-->>M: Publish EMG Data
    M-->>P: Forward EMG Data
    M-->>T: Forward EMG Data
    
    Note over P,B: Session Active
    P-->>B: Session status updates
```

### Pros
- Simpler to implement.
- Improves scalability
- Better suited for IoT data
- Designed for IoT

### Cons
- Higher latency
- Single point of failure. If broker fails data transmission is halted.

## Decision

Due to the nature of the emg data, option 2 has been selected as it is designed for sensor data and still provides
real time data access with the use of websockets.