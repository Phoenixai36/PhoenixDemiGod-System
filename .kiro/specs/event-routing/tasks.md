# Implementation Plan

- [x] 1. Set up project structure and core interfaces
  - ✅ Core interfaces and abstract base classes already exist in `src/phoenixxhydra/core/event_routing.py`
  - ✅ Type definitions and enums (DeliveryMode) already implemented
  - ✅ EventRouter, PatternMatcher, EventQueue interfaces defined
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement core data models
  - [x] 2.1 Create Event data model with validation
    - ✅ Event dataclass with all required fields already implemented
    - ✅ Validation methods for event data integrity already exist
    - ❌ Need to create unit tests for Event model validation and serialization
    - _Requirements: 1.1, 3.1, 3.4_

  - [x] 2.2 Implement EventPattern and Subscription models
    - ✅ EventPattern dataclass with wildcard and attribute filter support already implemented
    - ✅ Subscription dataclass with pattern and handler references already implemented
    - ❌ Need to write unit tests for pattern creation and subscription management
    - _Requirements: 2.1, 2.2, 2.5_

- [x] 3. Implement Pattern Matcher component
  - [x] 3.1 Create basic pattern matching functionality
    - ✅ PatternMatcher interface and DefaultPatternMatcher already implemented
    - ✅ Support for exact event type matching already exists
    - ❌ Need to write unit tests for basic pattern matching scenarios
    - _Requirements: 2.2, 2.3_

  - [x] 3.2 Add wildcard pattern support
    - ✅ WildcardPatternMatcher with single-level (*) and multi-level (**) wildcard matching already implemented
    - ❌ Need to create comprehensive unit tests for wildcard pattern scenarios
    - _Requirements: 2.4_

  - [x] 3.3 Implement attribute filtering
    - ✅ Support for exact attribute matching and comparison operators already implemented
    - ✅ Nested attribute path support already exists
    - ❌ Need to write unit tests for all attribute filtering scenarios
    - _Requirements: 2.5_

- [x] 1. Migrate existing implementation to proper location



  - Move existing event routing implementation from `src/phoenixxhydra/core/event_routing.py` to `src/event_routing/`
  - Create proper module structure under `src/event_routing/`
  - Update imports and references to use new location
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement Event Store component


  - [x] 2.1 Create in-memory event store implementation


    - Implement EventStore class with store() and get_events() methods
    - Add chronological ordering for event retrieval
    - Create unit tests for basic storage and retrieval operations
    - _Requirements: 4.1, 4.4_

  - [x] 2.2 Add event filtering and querying


    - Implement filter_criteria support in get_events() method
    - Add time-based filtering (start_time, end_time) for event queries
    - Create get_event_by_id() method for individual event retrieval
    - Write unit tests for all filtering and querying scenarios
    - _Requirements: 4.4_

  - [x] 2.3 Implement retention policy and cleanup


    - Create RetentionPolicy dataclass with age and count limits
    - Implement cleanup_expired_events() method with policy enforcement
    - Add support for event-type-specific retention policies
    - Write unit tests for retention policy enforcement
    - _Requirements: 4.5_

- [x] 3. Implement Event Correlator component

  - [ ] 3.1 Create correlation tracking functionality




    - Implement EventCorrelator class with correlate() method
    - Add unique correlation ID generation for new workflows
    - Create correlation chain storage and retrieval mechanisms
    - Write unit tests for correlation ID generation and tracking
    - _Requirements: 3.1, 3.4_

  - [x] 3.2 Implement correlation chain management


    - Add get_correlation_chain() method to retrieve related events
    - Implement causation_id tracking for event relationships
    - Create methods to associate events with existing correlations
    - Write unit tests for correlation chain retrieval and management
    - _Requirements: 3.2, 3.3, 3.5_

- [x] 4. Complete Event Router implementation


  - [x] 4.1 Complete publish/subscribe mechanism


    - ✅ Basic EventRouter class structure already exists
    - Complete publish() method with all delivery modes
    - Enhance subscribe() and unsubscribe() methods
    - Write unit tests for basic pub/sub functionality
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 4.2 Add synchronous and asynchronous delivery modes

    - ✅ DeliveryMode enum already implemented
    - Complete mode-specific delivery logic in publish() method
    - Add concurrent delivery for ASYNC mode using asyncio
    - Implement sequential delivery for SYNC mode with failure handling
    - Write unit tests for both delivery modes
    - _Requirements: 1.4_

  - [x] 4.3 Implement multi-subscriber delivery

    - Ensure events are delivered to all matching subscribers
    - Add proper error handling for individual subscriber failures
    - Implement delivery confirmation and failure tracking
    - Write unit tests for multi-subscriber scenarios
    - _Requirements: 1.5_

- [ ] 5. Integrate Pattern Matcher with Event Router
  - ✅ PatternMatcher already connected to EventRouter in existing implementation
  - Complete pattern-based event routing in publish() method
  - Add subscription pattern validation during subscribe() calls
  - Write integration tests for pattern-based event routing
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 6. Integrate Event Store with Event Router
  - Connect EventStore to EventRouter for automatic event persistence
  - Add event storage during publish() operations
  - Implement configurable storage policies (store all vs. selective)
  - Write integration tests for event storage during routing
  - _Requirements: 4.1_

- [ ] 7. Implement Event Replayer component
  - [ ] 7.1 Create basic replay functionality
    - Implement EventReplayer class with replay() method
    - Add event retrieval from EventStore with proper ordering
    - Create replay event marking (is_replay flag) to distinguish replayed events
    - Write unit tests for basic replay scenarios
    - _Requirements: 4.2, 4.3_

  - [ ] 7.2 Add filtered replay capabilities
    - Implement filter_criteria support in replay() method
    - Add time-based replay filtering (start_time, end_time)
    - Create event type and correlation-based replay filtering
    - Write unit tests for all replay filtering scenarios
    - _Requirements: 4.2, 4.4_

- [ ] 8. Implement Agent Hook Integration
  - [ ] 8.1 Create EventHookTrigger component
    - Implement EventHookTrigger class with register_hook() and unregister_hook() methods
    - Add hook subscription management and automatic event subscription creation
    - Create trigger_hook() method for executing hooks with events
    - Write unit tests for hook registration and triggering
    - _Requirements: 5.1, 5.5_

  - [ ] 8.2 Integrate with Phoenix Hydra agent hooks system
    - Connect EventHookTrigger with existing event bus in `src/hooks/core/events.py`
    - Add support for Phoenix Hydra event types (code.file.modified, container.health.unhealthy)
    - Implement hook response event publishing back to EventRouter
    - Write integration tests with Phoenix Hydra agent hooks framework
    - _Requirements: 5.2, 5.4_

  - [ ] 8.3 Add hook execution error handling
    - Implement proper error handling for hook execution failures
    - Add hook execution success/failure event publishing
    - Create hook subscription cleanup on hook failures
    - Write unit tests for hook error scenarios
    - _Requirements: 5.3_

- [ ] 9. Create comprehensive unit tests for existing components
  - [ ] 9.1 Write tests for Event model
    - Create unit tests for Event validation and serialization
    - Test event creation, derivation, and dictionary conversion
    - Add tests for correlation and causation ID handling
    - _Requirements: 1.1, 3.1, 3.4_

  - [ ] 9.2 Write tests for Pattern Matcher components
    - Create unit tests for basic pattern matching scenarios
    - Add comprehensive tests for wildcard pattern scenarios
    - Write tests for all attribute filtering scenarios
    - Test performance with CachedPatternMatcher
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 9.3 Write tests for Subscription management
    - Test subscription creation, activation, and expiration
    - Add tests for subscription priority and event processing
    - Write tests for subscription pattern matching
    - _Requirements: 1.2, 1.3_

- [ ] 10. Add comprehensive error handling
  - Implement error handling for subscription failures during event delivery
  - Add retry mechanisms for failed event deliveries with configurable policies
  - Create error event publishing for system monitoring
  - Write unit tests for all error handling scenarios
  - _Requirements: 1.1, 1.5_

- [ ] 11. Implement monitoring and observability
  - Add event throughput metrics collection
  - Implement subscription statistics tracking
  - Create pattern matching performance metrics
  - Add correlation tracking and replay operation metrics
  - Write unit tests for metrics collection
  - _Requirements: All requirements for system monitoring_

- [ ] 12. Create comprehensive integration tests
  - Write end-to-end tests for complete event flow (publish → route → deliver)
  - Create correlation tracking tests across multiple events
  - Implement replay functionality tests with various scenarios
  - Add agent hook integration tests with mock hooks
  - _Requirements: All requirements_

- [ ] 13. Add configuration and initialization
  - Create configuration classes for EventRouter, EventStore, and other components
  - Implement factory methods for component initialization
  - Add configuration validation and default value handling
  - Write unit tests for configuration and initialization
  - _Requirements: All requirements_

- [ ] 14. Wire components together and create main interface
  - Create main EventRoutingSystem class that orchestrates all components
  - Implement system startup and shutdown procedures
  - Add component health checking and status reporting
  - Create integration with Phoenix Hydra system initialization
  - Write system-level integration tests
  - _Requirements: All requirements_