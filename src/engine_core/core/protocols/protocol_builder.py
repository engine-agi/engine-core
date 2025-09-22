"""
Protocol Builder - Builder Pattern for Protocol Creation.

Provides a fluent interface for creating and configuring protocols
with semantic command processing capabilities in the Engine Framework.

Following the builder pattern established in the framework for consistency
and ease of use across all core components.
"""

from typing import Dict, Any, List, Optional, Union, Set, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .protocol import (
    ProtocolParser,
    IntentRecognizer,
    PatternBasedIntentRecognizer,
    CommandType,
    IntentCategory,
    ContextScope,
    CommandPriority,
    CommandContext,
    ParsedCommand,
    ExecutionPlan
)

# Type checking imports
if TYPE_CHECKING:
    from ..agents.agent_builder import BuiltAgent

logger = logging.getLogger(__name__)


@dataclass
class ProtocolConfiguration:
    """Configuration for protocol creation."""
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Parser configuration
    intent_recognizer: Optional[IntentRecognizer] = None
    supported_intents: List[IntentCategory] = field(default_factory=lambda: list(IntentCategory))
    supported_command_types: List[CommandType] = field(default_factory=lambda: list(CommandType))

    # Context configuration
    default_scope: ContextScope = ContextScope.SESSION
    max_context_history: int = 100
    context_timeout_seconds: int = 3600  # 1 hour

    # Validation configuration
    strict_validation: bool = False
    allow_unknown_intents: bool = True
    max_validation_errors: int = 10

    # Execution configuration
    max_execution_time: int = 300  # 5 minutes
    retry_attempts: int = 3
    enable_fallbacks: bool = True

    # Learning configuration
    enable_learning: bool = True
    learning_rate: float = 0.1
    confidence_threshold: float = 0.6

    # Custom extensions
    custom_validators: List[Callable] = field(default_factory=list)
    custom_transformers: List[Callable] = field(default_factory=list)
    custom_recognizers: List[IntentRecognizer] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuiltProtocol:
    """Built protocol with all components configured."""
    id: str
    configuration: ProtocolConfiguration
    parser: ProtocolParser
    statistics: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Get protocol name."""
        return self.configuration.name or self.id

    @property
    def description(self) -> str:
        """Get protocol description."""
        return self.configuration.description or f"Protocol {self.id}"

    async def parse_command(
        self,
        text: str,
        context: Optional['CommandContext'] = None
    ) -> 'ParsedCommand':
        """Parse a command using this protocol."""
        return await self.parser.parse_command(text, context)

    async def create_execution_plan(
        self,
        command: 'ParsedCommand',
        context: 'CommandContext',
        available_agents: Optional[List['BuiltAgent']] = None,
        available_tools: Optional[List[str]] = None
    ) -> 'ExecutionPlan':
        """Create execution plan for a command."""
        return await self.parser.create_execution_plan(
            command, context, available_agents, available_tools
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get protocol usage statistics."""
        stats = self.parser.get_parser_statistics()
        stats.update(self.statistics)
        return stats

    def update_statistics(self, key: str, value: Any) -> None:
        """Update protocol statistics."""
        self.statistics[key] = value
        self.configuration.updated_at = datetime.utcnow()


class ProtocolBuilder:
    """
    Builder for creating protocols with semantic command processing.

    Provides a fluent interface for configuring protocol components including:
    - Intent recognition and parsing
    - Context analysis and management
    - Command validation and execution planning
    - Learning and adaptation capabilities

    Example:
        protocol = (ProtocolBuilder()
            .with_id("analysis_protocol")
            .with_name("Advanced Analysis Protocol")
            .with_supported_intents([IntentCategory.ANALYZE, IntentCategory.GENERATE])
            .with_default_scope(ContextScope.PROJECT)
            .with_strict_validation(True)
            .with_custom_intent_recognizer(MyRecognizer())
            .build())
    """

    def __init__(self):
        """Initialize protocol builder with defaults."""
        self._config = ProtocolConfiguration(
            id="",
            supported_intents=list(IntentCategory),
            supported_command_types=list(CommandType)
        )
        self._custom_recognizers: List[IntentRecognizer] = []
        self._validators: List[Callable] = []
        self._transformers: List[Callable] = []

    def with_id(self, protocol_id: str) -> 'ProtocolBuilder':
        """Set protocol ID."""
        if not protocol_id or not protocol_id.strip():
            raise ValueError("Protocol ID cannot be empty")
        self._config.id = protocol_id.strip()
        return self

    def with_name(self, name: str) -> 'ProtocolBuilder':
        """Set protocol name."""
        self._config.name = name
        return self

    def with_description(self, description: str) -> 'ProtocolBuilder':
        """Set protocol description."""
        self._config.description = description
        return self

    def with_version(self, version: str) -> 'ProtocolBuilder':
        """Set protocol version."""
        self._config.version = version
        return self

    def with_author(self, author: str) -> 'ProtocolBuilder':
        """Set protocol author."""
        self._config.author = author
        return self

    def with_tags(self, tags: List[str]) -> 'ProtocolBuilder':
        """Set protocol tags."""
        self._config.tags = tags
        return self

    def with_supported_intents(self, intents: List[IntentCategory]) -> 'ProtocolBuilder':
        """Set supported intent categories."""
        self._config.supported_intents = intents
        return self

    def with_supported_command_types(self, command_types: List[CommandType]) -> 'ProtocolBuilder':
        """Set supported command types."""
        self._config.supported_command_types = command_types
        return self

    def with_default_scope(self, scope: ContextScope) -> 'ProtocolBuilder':
        """Set default context scope."""
        self._config.default_scope = scope
        return self

    def with_max_context_history(self, max_history: int) -> 'ProtocolBuilder':
        """Set maximum context history size."""
        if max_history < 0:
            raise ValueError("Max context history must be non-negative")
        self._config.max_context_history = max_history
        return self

    def with_context_timeout(self, timeout_seconds: int) -> 'ProtocolBuilder':
        """Set context timeout in seconds."""
        if timeout_seconds < 0:
            raise ValueError("Context timeout must be non-negative")
        self._config.context_timeout_seconds = timeout_seconds
        return self

    def with_strict_validation(self, strict: bool = True) -> 'ProtocolBuilder':
        """Enable strict validation mode."""
        self._config.strict_validation = strict
        return self

    def with_allow_unknown_intents(self, allow: bool = True) -> 'ProtocolBuilder':
        """Allow or disallow unknown intents."""
        self._config.allow_unknown_intents = allow
        return self

    def with_max_validation_errors(self, max_errors: int) -> 'ProtocolBuilder':
        """Set maximum validation errors before failing."""
        if max_errors < 0:
            raise ValueError("Max validation errors must be non-negative")
        self._config.max_validation_errors = max_errors
        return self

    def with_max_execution_time(self, max_time: int) -> 'ProtocolBuilder':
        """Set maximum execution time in seconds."""
        if max_time < 0:
            raise ValueError("Max execution time must be non-negative")
        self._config.max_execution_time = max_time
        return self

    def with_retry_attempts(self, attempts: int) -> 'ProtocolBuilder':
        """Set number of retry attempts."""
        if attempts < 0:
            raise ValueError("Retry attempts must be non-negative")
        self._config.retry_attempts = attempts
        return self

    def with_fallbacks_enabled(self, enabled: bool = True) -> 'ProtocolBuilder':
        """Enable or disable fallback plans."""
        self._config.enable_fallbacks = enabled
        return self

    def with_learning_enabled(self, enabled: bool = True) -> 'ProtocolBuilder':
        """Enable or disable learning capabilities."""
        self._config.enable_learning = enabled
        return self

    def with_learning_rate(self, rate: float) -> 'ProtocolBuilder':
        """Set learning rate for adaptation."""
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Learning rate must be between 0.0 and 1.0")
        self._config.learning_rate = rate
        return self

    def with_confidence_threshold(self, threshold: float) -> 'ProtocolBuilder':
        """Set confidence threshold for intent recognition."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        self._config.confidence_threshold = threshold
        return self

    def with_custom_intent_recognizer(self, recognizer: IntentRecognizer) -> 'ProtocolBuilder':
        """Add custom intent recognizer."""
        self._custom_recognizers.append(recognizer)
        return self

    def with_custom_validator(self, validator: Callable) -> 'ProtocolBuilder':
        """Add custom command validator."""
        self._validators.append(validator)
        return self

    def with_custom_transformer(self, transformer: Callable) -> 'ProtocolBuilder':
        """Add custom command transformer."""
        self._transformers.append(transformer)
        return self

    def with_metadata(self, key: str, value: Any) -> 'ProtocolBuilder':
        """Add metadata to protocol configuration."""
        self._config.metadata[key] = value
        return self

    def build(self) -> BuiltProtocol:
        """Build the protocol with current configuration."""
        if not self._config.id:
            raise ValueError("Protocol ID is required")

        # Create intent recognizer
        intent_recognizer = self._create_intent_recognizer()

        # Create protocol parser
        parser = ProtocolParser(intent_recognizer=intent_recognizer)

        # Apply configuration to parser if needed
        self._configure_parser(parser)

        # Create built protocol
        built_protocol = BuiltProtocol(
            id=self._config.id,
            configuration=self._config,
            parser=parser
        )

        logger.info(f"Built protocol '{built_protocol.id}' with {len(self._config.supported_intents)} supported intents")
        return built_protocol

    def _create_intent_recognizer(self) -> IntentRecognizer:
        """Create intent recognizer based on configuration."""
        if self._custom_recognizers:
            # Use custom recognizer if provided
            return self._custom_recognizers[0]  # Use first custom recognizer
        else:
            # Use default pattern-based recognizer
            return PatternBasedIntentRecognizer()

    def _configure_parser(self, parser: ProtocolParser) -> None:
        """Apply configuration settings to parser."""
        # This would configure the parser with the builder settings
        # For now, the parser uses its default configuration
        # Future enhancement: make parser configurable
        pass

    @classmethod
    def create_basic_protocol(cls, protocol_id: str, name: Optional[str] = None) -> BuiltProtocol:
        """Create a basic protocol with default settings."""
        return (cls()
            .with_id(protocol_id)
            .with_name(name or f"Basic Protocol {protocol_id}")
            .build())

    @classmethod
    def create_analysis_protocol(cls, protocol_id: str) -> BuiltProtocol:
        """Create a protocol optimized for analysis commands."""
        return (cls()
            .with_id(protocol_id)
            .with_name(f"Analysis Protocol {protocol_id}")
            .with_supported_intents([
                IntentCategory.ANALYZE,
                IntentCategory.QUERY,
                IntentCategory.READ
            ])
            .with_default_scope(ContextScope.PROJECT)
            .with_strict_validation(True)
            .build())

    @classmethod
    def create_generation_protocol(cls, protocol_id: str) -> BuiltProtocol:
        """Create a protocol optimized for generation commands."""
        return (cls()
            .with_id(protocol_id)
            .with_name(f"Generation Protocol {protocol_id}")
            .with_supported_intents([
                IntentCategory.GENERATE,
                IntentCategory.CREATE,
                IntentCategory.TRANSFORM
            ])
            .with_default_scope(ContextScope.WORKFLOW)
            .with_learning_enabled(True)
            .build())

    @classmethod
    def create_coordination_protocol(cls, protocol_id: str) -> BuiltProtocol:
        """Create a protocol optimized for coordination commands."""
        return (cls()
            .with_id(protocol_id)
            .with_name(f"Coordination Protocol {protocol_id}")
            .with_supported_intents([
                IntentCategory.COORDINATE,
                IntentCategory.EXECUTE,
                IntentCategory.CONTROL
            ])
            .with_default_scope(ContextScope.TEAM)
            .with_max_execution_time(600)  # 10 minutes
            .with_retry_attempts(5)
            .build())