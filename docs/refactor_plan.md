# Weather Alert System Refactoring Plan

## Current System Analysis

The current system has performance bottlenecks due to its sequential nature:
1. Makes request to NWS API
2. Processes each alert sequentially
3. Waits for API cooldown
4. Repeats cycle

This creates noticeable delays in both alert counter updates and live alert displays.

## Proposed Architecture

### Overview
Split the system into two independent but cooperating services using asyncio and a message queue system:

1. **Alert Fetcher Service**
   - Handles NWS API communication
   - Quick initial processing of alerts
   - Maintains alert counter
   - Pushes alerts to message queue

2. **Alert Display Service**
   - Consumes alerts from queue
   - Handles OBS interactions
   - Manages alert display logic
   - Runs independently of fetch timing

### Technical Components

1. **Message Queue**
   - Use Redis for inter-process communication
   - Provides reliable, fast message passing
   - Supports multiple consumers
   - Built-in persistence

2. **Async Processing**
   - Use Python's asyncio for non-blocking operations
   - Separate event loops for fetcher and display services
   - Concurrent processing of alerts

3. **Alert Processing Pipeline**
```
[NWS API] -> [Fetcher Service] -> [Redis Queue] -> [Display Service] -> [OBS]
```

### Benefits

1. **Improved Responsiveness**
   - Alert counter updates immediately after fetch
   - No blocking between fetch and display
   - Smooth alert display regardless of fetch status

2. **Better Resource Utilization**
   - Parallel processing of alerts
   - Independent scaling of services
   - No interdependence between fetch and display timing

3. **Enhanced Reliability**
   - Queue buffers alerts during high load
   - Services can restart independently
   - No data loss during processing

## Implementation Strategy

### Phase 1: Setup Foundation
- Implement Redis message queue
- Create base async service classes
- Setup logging and monitoring

### Phase 2: Alert Fetcher Service
- Implement async NWS API client
- Create alert processing pipeline
- Setup counter update mechanism

### Phase 3: Display Service
- Implement queue consumer
- Create async OBS connector
- Develop display logic

### Phase 4: Integration
- Connect services via Redis
- Implement error handling
- Add monitoring and metrics

## Migration Plan

1. Develop new system alongside existing
2. Test with production data copy
3. Gradual rollout with fallback option
4. Monitor and optimize performance

## Technical Requirements

- Python 3.10+
- Redis server
- aiohttp for async HTTP
- obs-websocket-py
- asyncio
- aioredis
