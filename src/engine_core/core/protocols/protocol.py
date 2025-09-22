"""
Protocol Parser - Semantic Command Processing System.

The ProtocolParser implements intelligent command interpretation and execution
for AI agents, providing semantic understanding of natural language commands
and mapping them to executable actions within the Engine Framework.

Key Features:
- Semantic command parsing with intent recognition
- Context-aware command interpretation
- Protocol validation and execution planning
- Dynamic command composition and chaining
- Multi-modal command support (text, structured, hybrid)
- Agent capability matching and routing
- Command history and learning
- Error recovery and suggestion system

Architecture:
- Intent Recognition: NLP-based command understanding
- Context Matching: Situational awareness and state tracking
- Action Planning: Command decomposition and execution planning
- Capability Routing: Agent/tool matching based on requirements
- Execution Orchestration: Command execution with workflow integration

Based on semantic parsing principles and adapted for AI agent orchestration.
"""

from typing import Dict, Any, List, Optional, Union, Set, Tuple, Callable, TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import uuid
import logging
from datetime import datetime
from functools import lru_cache
import asyncio

# Type checking imports
if TYPE_CHECKING:
    from ...models.protocol import Protocol
    from ...models.agent import Agent
    from ...models.team import Team
    from ..agents.agent_builder import BuiltAgent
    from ..teams.team_builder import BuiltTeam

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of protocol commands."""
    ANALYSIS = "analysis"
    GENERATION = "generation"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    EXECUTION = "execution"
    COORDINATION = "coordination"
    QUERY = "query"
    CONTROL = "control"


class IntentCategory(Enum):
    """Categories of user intent."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ANALYZE = "analyze"
    GENERATE = "generate"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    EXECUTE = "execute"
    COORDINATE = "coordinate"
    QUERY = "query"
    CONTROL = "control"


class ContextScope(Enum):
    """Scope of command context."""
    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"
    WORKFLOW = "workflow"
    AGENT = "agent"
    TEAM = "team"
    LOCAL = "local"


class CommandPriority(Enum):
    """Command execution priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


@dataclass
class CommandIntent:
    """Parsed command intent."""
    category: IntentCategory
    action: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    modifiers: List[str] = field(default_factory=list)
    confidence: float = 0.0
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert intent to dictionary."""
        return {
            'category': self.category.value,
            'action': self.action,
            'target': self.target,
            'parameters': self.parameters,
            'modifiers': self.modifiers,
            'confidence': self.confidence,
            'alternatives': self.alternatives
        }


@dataclass
class CommandContext:
    """Context for command execution."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    team_id: Optional[str] = None
    scope: ContextScope = ContextScope.SESSION
    variables: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'project_id': self.project_id,
            'workflow_id': self.workflow_id,
            'agent_id': self.agent_id,
            'team_id': self.team_id,
            'scope': self.scope.value,
            'variables': self.variables,
            'history': self.history,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ParsedCommand:
    """Result of command parsing."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_text: str = ""
    normalized_text: str = ""
    intent: Optional[CommandIntent] = None
    command_type: Optional[CommandType] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: CommandPriority = CommandPriority.NORMAL
    timeout_seconds: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if command is valid."""
        return len(self.validation_errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parsed command to dictionary."""
        return {
            'id': self.id,
            'original_text': self.original_text,
            'normalized_text': self.normalized_text,
            'intent': self.intent.to_dict() if self.intent else None,
            'command_type': self.command_type.value if self.command_type else None,
            'parameters': self.parameters,
            'requirements': self.requirements,
            'constraints': self.constraints,
            'priority': self.priority.value,
            'timeout_seconds': self.timeout_seconds,
            'dependencies': self.dependencies,
            'validation_errors': self.validation_errors,
            'suggestions': self.suggestions,
            'is_valid': self.is_valid
        }


@dataclass
class ExecutionPlan:
    """Plan for command execution."""
    command_id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    agents_required: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    complexity_score: float = 0.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    fallback_plans: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution plan to dictionary."""
        return {
            'command_id': self.command_id,
            'steps': self.steps,
            'agents_required': self.agents_required,
            'tools_required': self.tools_required,
            'estimated_duration': self.estimated_duration,
            'complexity_score': self.complexity_score,
            'resource_requirements': self.resource_requirements,
            'fallback_plans': self.fallback_plans
        }


class IntentRecognizer(ABC):
    """Abstract base class for intent recognition."""
    
    @abstractmethod
    async def recognize_intent(
        self,
        text: str,
        context: CommandContext
    ) -> CommandIntent:
        """Recognize intent from text and context."""
        pass
    
    @abstractmethod
    def get_supported_intents(self) -> List[IntentCategory]:
        """Get list of supported intent categories."""
        pass


class PatternBasedIntentRecognizer(IntentRecognizer):
    """Pattern-based intent recognizer using regex and keyword matching."""
    
    def __init__(self):
        """Initialize pattern-based recognizer."""
        self.patterns = self._initialize_patterns()
        self.keywords = self._initialize_keywords()
    
    def _initialize_patterns(self) -> Dict[IntentCategory, List[str]]:
        """Initialize regex patterns for intent recognition."""
        return {
            IntentCategory.CREATE: [
                r'\b(create|make|build|new|add)\s+(.+)',
                r'\bI\s+(want|need)\s+to\s+(create|make|build)\s+(.+)',
                r'\bLet\'?s\s+(create|make|build)\s+(.+)'
            ],
            IntentCategory.READ: [
                r'\b(show|display|get|fetch|read|list|find)\s+(.+)',
                r'\bWhat\s+(is|are)\s+(.+)\?',
                r'\bTell\s+me\s+about\s+(.+)',
                r'\bI\s+want\s+to\s+(see|view|check)\s+(.+)'
            ],
            IntentCategory.UPDATE: [
                r'\b(update|modify|change|edit|alter)\s+(.+)',
                r'\bI\s+want\s+to\s+(update|modify|change)\s+(.+)',
                r'\bCan\s+you\s+(update|modify|change)\s+(.+)\?'
            ],
            IntentCategory.DELETE: [
                r'\b(delete|remove|drop|clear)\s+(.+)',
                r'\bI\s+want\s+to\s+(delete|remove)\s+(.+)',
                r'\bCan\s+you\s+(delete|remove)\s+(.+)\?'
            ],
            IntentCategory.ANALYZE: [
                r'\b(analyze|examine|study|investigate|review)\s+(.+)',
                r'\bWhat\s+does\s+(.+)\s+mean\?',
                r'\bI\s+need\s+an?\s+analysis\s+of\s+(.+)',
                r'\bCan\s+you\s+analyze\s+(.+)\?'
            ],
            IntentCategory.GENERATE: [
                r'\b(generate|produce|synthesize|compose|write)\s+(.+)',
                r'\bI\s+need\s+you\s+to\s+(generate|produce|write)\s+(.+)',
                r'\bCan\s+you\s+(generate|produce|create)\s+(.+)\?'
            ],
            IntentCategory.TRANSFORM: [
                r'\b(transform|convert|translate|adapt|migrate)\s+(.+)',
                r'\bConvert\s+(.+)\s+to\s+(.+)',
                r'\bI\s+want\s+to\s+(transform|convert)\s+(.+)'
            ],
            IntentCategory.VALIDATE: [
                r'\b(validate|verify|check|test|confirm)\s+(.+)',
                r'\bIs\s+(.+)\s+(valid|correct|right)\?',
                r'\bCan\s+you\s+(validate|verify|check)\s+(.+)\?'
            ],
            IntentCategory.EXECUTE: [
                r'\b(execute|run|perform|do|start)\s+(.+)',
                r'\bI\s+want\s+to\s+(execute|run|start)\s+(.+)',
                r'\bCan\s+you\s+(execute|run|perform)\s+(.+)\?'
            ],
            IntentCategory.COORDINATE: [
                r'\b(coordinate|orchestrate|manage|organize)\s+(.+)',
                r'\bI\s+need\s+to\s+(coordinate|organize)\s+(.+)',
                r'\bCan\s+you\s+(coordinate|manage)\s+(.+)\?'
            ],
            IntentCategory.QUERY: [
                r'\b(query|search|find|lookup|retrieve)\s+(.+)',
                r'\bWhat\s+(.+)\s+(contains|has|includes)\?',
                r'\bCan\s+you\s+(search|find|lookup)\s+(.+)\?'
            ],
            IntentCategory.CONTROL: [
                r'\b(stop|pause|resume|cancel|abort)\s+(.+)',
                r'\bI\s+want\s+to\s+(stop|pause|cancel)\s+(.+)',
                r'\bCan\s+you\s+(stop|pause|resume)\s+(.+)\?'
            ]
        }
    
    def _initialize_keywords(self) -> Dict[IntentCategory, List[str]]:
        """Initialize keyword sets for intent recognition."""
        return {
            IntentCategory.CREATE: ['create', 'make', 'build', 'generate', 'new', 'add', 'construct'],
            IntentCategory.READ: ['show', 'display', 'get', 'fetch', 'read', 'list', 'view', 'see'],
            IntentCategory.UPDATE: ['update', 'modify', 'change', 'edit', 'alter', 'adjust'],
            IntentCategory.DELETE: ['delete', 'remove', 'drop', 'clear', 'destroy', 'eliminate'],
            IntentCategory.ANALYZE: ['analyze', 'examine', 'study', 'investigate', 'review', 'assess'],
            IntentCategory.GENERATE: ['generate', 'produce', 'synthesize', 'compose', 'write', 'create'],
            IntentCategory.TRANSFORM: ['transform', 'convert', 'translate', 'adapt', 'migrate', 'change'],
            IntentCategory.VALIDATE: ['validate', 'verify', 'check', 'test', 'confirm', 'ensure'],
            IntentCategory.EXECUTE: ['execute', 'run', 'perform', 'do', 'start', 'launch'],
            IntentCategory.COORDINATE: ['coordinate', 'orchestrate', 'manage', 'organize', 'sync'],
            IntentCategory.QUERY: ['query', 'search', 'find', 'lookup', 'retrieve', 'locate'],
            IntentCategory.CONTROL: ['stop', 'pause', 'resume', 'cancel', 'abort', 'halt']
        }
    
    async def recognize_intent(
        self,
        text: str,
        context: CommandContext
    ) -> CommandIntent:
        """Recognize intent using pattern matching and keywords."""
        
        normalized_text = text.lower().strip()
        best_match = None
        best_confidence = 0.0
        
        # Try pattern matching first
        for intent_category, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, normalized_text, re.IGNORECASE)
                if match:
                    confidence = 0.8 + (len(match.group(0)) / len(text)) * 0.2
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        
                        # Extract action and target from match groups
                        groups = match.groups()
                        action = groups[0] if groups else intent_category.value
                        target = groups[1] if len(groups) > 1 else None
                        
                        best_match = CommandIntent(
                            category=intent_category,
                            action=action,
                            target=target,
                            confidence=confidence
                        )
        
        # Fallback to keyword matching
        if best_confidence < 0.5:
            keyword_scores = {}
            words = normalized_text.split()
            
            for intent_category, keywords in self.keywords.items():
                score = sum(1 for word in words if word in keywords)
                if score > 0:
                    keyword_scores[intent_category] = score / len(words)
            
            if keyword_scores:
                best_intent = max(keyword_scores.items(), key=lambda x: x[1])[0]
                confidence = keyword_scores[best_intent] * 0.6
                
                if confidence > best_confidence:
                    best_match = CommandIntent(
                        category=best_intent,
                        action=best_intent.value,
                        confidence=confidence
                    )
        
        # Default fallback
        if not best_match:
            best_match = CommandIntent(
                category=IntentCategory.QUERY,
                action="process",
                confidence=0.1
            )
        
        # Add context-based adjustments
        if context.history:
            # Boost confidence if similar commands were used recently
            recent_intents = [
                cmd.get('intent', {}).get('category') 
                for cmd in context.history[-5:]
            ]
            if best_match.category.value in recent_intents:
                best_match.confidence = min(1.0, best_match.confidence + 0.1)
        
        return best_match
    
    def get_supported_intents(self) -> List[IntentCategory]:
        """Get list of supported intent categories."""
        return list(IntentCategory)


class ContextAnalyzer:
    """Analyzes and enriches command context."""
    
    def __init__(self):
        """Initialize context analyzer."""
        self.variable_patterns = {
            'file_path': r'\b[\w\-_./]+\.(py|js|ts|json|yaml|yml|md|txt)\b',
            'url': r'https?://[^\s]+',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'number': r'\b\d+\.?\d*\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'agent_reference': r'@\w+',
            'variable_reference': r'\$\{?\w+\}?'
        }
    
    async def analyze_context(
        self,
        text: str,
        base_context: CommandContext
    ) -> CommandContext:
        """Analyze and enrich command context."""
        
        enhanced_context = CommandContext(
            user_id=base_context.user_id,
            session_id=base_context.session_id,
            project_id=base_context.project_id,
            workflow_id=base_context.workflow_id,
            agent_id=base_context.agent_id,
            team_id=base_context.team_id,
            scope=base_context.scope,
            variables=base_context.variables.copy(),
            history=base_context.history.copy(),
            metadata=base_context.metadata.copy()
        )
        
        # Extract variables from text
        extracted_vars = self._extract_variables(text)
        enhanced_context.variables.update(extracted_vars)
        
        # Analyze scope requirements
        scope = self._analyze_scope_requirements(text, base_context)
        enhanced_context.scope = scope
        
        # Add metadata
        enhanced_context.metadata.update({
            'text_length': len(text),
            'word_count': len(text.split()),
            'has_questions': '?' in text,
            'has_references': any(pattern in text for pattern in ['@', '$', 'http']),
            'command_complexity': self._calculate_complexity(text)
        })
        
        return enhanced_context
    
    def _extract_variables(self, text: str) -> Dict[str, Any]:
        """Extract variables and references from text."""
        variables = {}
        
        for var_type, pattern in self.variable_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                variables[f'{var_type}_found'] = matches
        
        return variables
    
    def _analyze_scope_requirements(
        self,
        text: str,
        context: CommandContext
    ) -> ContextScope:
        """Analyze required context scope."""
        
        if any(keyword in text.lower() for keyword in ['global', 'all', 'everything', 'system']):
            return ContextScope.GLOBAL
        elif any(keyword in text.lower() for keyword in ['project', 'repository', 'repo']):
            return ContextScope.PROJECT
        elif any(keyword in text.lower() for keyword in ['workflow', 'process', 'pipeline']):
            return ContextScope.WORKFLOW
        elif any(keyword in text.lower() for keyword in ['team', 'group', 'members']):
            return ContextScope.TEAM
        elif any(keyword in text.lower() for keyword in ['agent', 'assistant', 'bot']):
            return ContextScope.AGENT
        elif any(keyword in text.lower() for keyword in ['here', 'this', 'current']):
            return ContextScope.LOCAL
        else:
            return context.scope or ContextScope.SESSION
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate command complexity score."""
        
        factors = {
            'length': len(text) / 1000,  # Normalize by character count
            'words': len(text.split()) / 100,  # Normalize by word count
            'questions': text.count('?') * 0.1,
            'conjunctions': len(re.findall(r'\b(and|or|but|if|then|else|when|while)\b', text, re.IGNORECASE)) * 0.2,
            'references': len(re.findall(r'[@$#]', text)) * 0.1,
            'technical_terms': len(re.findall(r'\b(function|class|method|variable|database|api|service)\b', text, re.IGNORECASE)) * 0.15
        }
        
        return min(1.0, sum(factors.values()))


class CommandValidator:
    """Validates parsed commands and provides suggestions."""
    
    def __init__(self):
        """Initialize command validator."""
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> Dict[CommandType, List[Callable]]:
        """Initialize validation rules for each command type."""
        return {
            CommandType.ANALYSIS: [
                self._validate_has_target,
                self._validate_analysis_type
            ],
            CommandType.GENERATION: [
                self._validate_has_output_spec,
                self._validate_generation_type
            ],
            CommandType.TRANSFORMATION: [
                self._validate_has_input_output,
                self._validate_transformation_type
            ],
            CommandType.VALIDATION: [
                self._validate_has_target,
                self._validate_validation_criteria
            ],
            CommandType.EXECUTION: [
                self._validate_executable_target,
                self._validate_execution_permissions
            ],
            CommandType.COORDINATION: [
                self._validate_has_agents_or_teams,
                self._validate_coordination_type
            ],
            CommandType.QUERY: [
                self._validate_has_query_target,
                self._validate_query_scope
            ],
            CommandType.CONTROL: [
                self._validate_control_target,
                self._validate_control_action
            ]
        }
    
    async def validate_command(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> ParsedCommand:
        """Validate parsed command and add suggestions."""
        
        errors = []
        suggestions = []
        
        # Basic validation
        if not command.original_text.strip():
            errors.append("Command cannot be empty")
        
        if not command.intent:
            errors.append("Unable to understand command intent")
            suggestions.append("Try rephrasing your command more clearly")
        
        # Type-specific validation
        if command.command_type and command.command_type in self.validation_rules:
            rules = self.validation_rules[command.command_type]
            
            for rule in rules:
                try:
                    rule_errors, rule_suggestions = await rule(command, context)
                    errors.extend(rule_errors)
                    suggestions.extend(rule_suggestions)
                except Exception as e:
                    logger.error(f"Validation rule failed: {str(e)}")
                    errors.append(f"Validation error: {str(e)}")
        
        # Context validation
        context_errors, context_suggestions = await self._validate_context(command, context)
        errors.extend(context_errors)
        suggestions.extend(context_suggestions)
        
        # Update command with validation results
        command.validation_errors = errors
        command.suggestions = suggestions
        
        return command
    
    async def _validate_has_target(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate command has a target."""
        errors = []
        suggestions = []
        
        if not command.intent or not command.intent.target:
            if not command.parameters.get('target'):
                errors.append("Command requires a target to operate on")
                suggestions.append("Specify what you want to analyze/process")
        
        return errors, suggestions
    
    async def _validate_analysis_type(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate analysis command specifics."""
        errors = []
        suggestions = []
        
        valid_analysis_types = ['code', 'data', 'text', 'performance', 'security']
        analysis_type = command.parameters.get('analysis_type')
        
        if analysis_type and analysis_type not in valid_analysis_types:
            errors.append(f"Unknown analysis type: {analysis_type}")
            suggestions.append(f"Try one of: {', '.join(valid_analysis_types)}")
        
        return errors, suggestions
    
    async def _validate_has_output_spec(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate generation command has output specification."""
        errors = []
        suggestions = []
        
        if not command.parameters.get('output_format') and not command.parameters.get('output_type'):
            suggestions.append("Consider specifying the desired output format")
        
        return errors, suggestions
    
    async def _validate_generation_type(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate generation command type."""
        errors = []
        suggestions = []
        
        valid_generation_types = ['code', 'documentation', 'test', 'data', 'report']
        generation_type = command.parameters.get('generation_type')
        
        if generation_type and generation_type not in valid_generation_types:
            errors.append(f"Unknown generation type: {generation_type}")
            suggestions.append(f"Try one of: {', '.join(valid_generation_types)}")
        
        return errors, suggestions
    
    async def _validate_has_input_output(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate transformation has input and output specs."""
        errors = []
        suggestions = []
        
        if not command.parameters.get('input_format') and not command.parameters.get('from'):
            suggestions.append("Specify the input format or source")
        
        if not command.parameters.get('output_format') and not command.parameters.get('to'):
            suggestions.append("Specify the output format or target")
        
        return errors, suggestions
    
    async def _validate_transformation_type(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate transformation type."""
        errors = []
        suggestions = []
        
        valid_transformation_types = ['format', 'language', 'structure', 'protocol']
        transformation_type = command.parameters.get('transformation_type')
        
        if transformation_type and transformation_type not in valid_transformation_types:
            errors.append(f"Unknown transformation type: {transformation_type}")
            suggestions.append(f"Try one of: {', '.join(valid_transformation_types)}")
        
        return errors, suggestions
    
    async def _validate_validation_criteria(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate validation command criteria."""
        errors = []
        suggestions = []
        
        if not command.parameters.get('criteria') and not command.parameters.get('rules'):
            suggestions.append("Consider specifying validation criteria or rules")
        
        return errors, suggestions
    
    async def _validate_executable_target(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate execution target is executable."""
        errors = []
        suggestions = []
        
        target = command.intent.target if command.intent else None
        if not target and not command.parameters.get('script') and not command.parameters.get('command'):
            errors.append("Execution requires a target script, command, or workflow")
            suggestions.append("Specify what you want to execute")
        
        return errors, suggestions
    
    async def _validate_execution_permissions(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate execution permissions."""
        errors = []
        suggestions = []
        
        # In a real implementation, this would check actual permissions
        if command.parameters.get('requires_admin') and not context.metadata.get('has_admin_rights'):
            errors.append("Command requires administrator privileges")
            suggestions.append("Request elevated permissions or contact administrator")
        
        return errors, suggestions
    
    async def _validate_has_agents_or_teams(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate coordination command has agents or teams."""
        errors = []
        suggestions = []
        
        if not command.parameters.get('agents') and not command.parameters.get('teams'):
            if not context.agent_id and not context.team_id:
                errors.append("Coordination requires agents or teams to coordinate")
                suggestions.append("Specify which agents or teams to coordinate")
        
        return errors, suggestions
    
    async def _validate_coordination_type(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate coordination type."""
        errors = []
        suggestions = []
        
        valid_coordination_types = ['sequential', 'parallel', 'hierarchical', 'collaborative']
        coordination_type = command.parameters.get('coordination_type')
        
        if coordination_type and coordination_type not in valid_coordination_types:
            errors.append(f"Unknown coordination type: {coordination_type}")
            suggestions.append(f"Try one of: {', '.join(valid_coordination_types)}")
        
        return errors, suggestions
    
    async def _validate_has_query_target(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate query has target."""
        errors = []
        suggestions = []
        
        if not command.intent or not command.intent.target:
            if not command.parameters.get('query') and not command.parameters.get('search_terms'):
                errors.append("Query requires search terms or target")
                suggestions.append("Specify what you want to search for")
        
        return errors, suggestions
    
    async def _validate_query_scope(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate query scope."""
        errors = []
        suggestions = []
        
        valid_scopes = ['global', 'project', 'session', 'workflow', 'agent', 'team', 'local']
        scope = command.parameters.get('scope')
        
        if scope and scope not in valid_scopes:
            errors.append(f"Unknown query scope: {scope}")
            suggestions.append(f"Try one of: {', '.join(valid_scopes)}")
        
        return errors, suggestions
    
    async def _validate_control_target(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate control command target."""
        errors = []
        suggestions = []
        
        if not command.intent or not command.intent.target:
            if not command.parameters.get('target_id'):
                errors.append("Control command requires a target to control")
                suggestions.append("Specify what process, workflow, or agent to control")
        
        return errors, suggestions
    
    async def _validate_control_action(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate control action."""
        errors = []
        suggestions = []
        
        valid_actions = ['start', 'stop', 'pause', 'resume', 'cancel', 'restart']
        action = command.intent.action if command.intent else None
        
        if action and action not in valid_actions:
            errors.append(f"Unknown control action: {action}")
            suggestions.append(f"Try one of: {', '.join(valid_actions)}")
        
        return errors, suggestions
    
    async def _validate_context(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Tuple[List[str], List[str]]:
        """Validate command context requirements."""
        errors = []
        suggestions = []
        
        # Check required context fields
        if command.requirements:
            for requirement in command.requirements:
                if requirement == 'project' and not context.project_id:
                    errors.append("Command requires a project context")
                    suggestions.append("Set project context or specify project ID")
                elif requirement == 'agent' and not context.agent_id:
                    errors.append("Command requires an agent context")
                    suggestions.append("Select an agent or specify agent ID")
                elif requirement == 'team' and not context.team_id:
                    errors.append("Command requires a team context")
                    suggestions.append("Select a team or specify team ID")
        
        return errors, suggestions


class ProtocolParser:
    """
    Main protocol parser for semantic command processing.
    
    Coordinates intent recognition, context analysis, command validation,
    and execution planning to provide intelligent command interpretation
    for AI agents in the Engine Framework.
    
    Key Components:
    - Intent Recognition: Understanding what the user wants to do
    - Context Analysis: Understanding the situational context
    - Command Validation: Ensuring commands are valid and executable
    - Execution Planning: Creating actionable execution plans
    - Capability Matching: Finding appropriate agents/tools for execution
    """
    
    def __init__(
        self,
        intent_recognizer: Optional[IntentRecognizer] = None
    ):
        """Initialize protocol parser."""
        self.intent_recognizer = intent_recognizer or PatternBasedIntentRecognizer()
        self.context_analyzer = ContextAnalyzer()
        self.command_validator = CommandValidator()
        
        # Statistics
        self.parser_stats = {
            'total_commands_parsed': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'average_parse_time': 0.0,
            'intent_accuracy': 0.0
        }
        
        # Cache for frequent patterns
        self._pattern_cache = {}
    
    async def parse_command(
        self,
        text: str,
        context: Optional[CommandContext] = None
    ) -> ParsedCommand:
        """Parse natural language command into structured format."""
        start_time = datetime.utcnow()
        
        try:
            # Initialize context if not provided
            if context is None:
                context = CommandContext()
            
            # Normalize text
            normalized_text = self._normalize_text(text)
            
            # Analyze context
            enhanced_context = await self.context_analyzer.analyze_context(text, context)
            
            # Recognize intent
            intent = await self.intent_recognizer.recognize_intent(text, enhanced_context)
            
            # Create parsed command
            parsed_command = ParsedCommand(
                original_text=text,
                normalized_text=normalized_text,
                intent=intent
            )
            
            # Determine command type
            parsed_command.command_type = self._map_intent_to_command_type(intent)
            
            # Extract parameters
            parsed_command.parameters = await self._extract_parameters(text, intent, enhanced_context)
            
            # Determine requirements and constraints
            parsed_command.requirements = self._determine_requirements(intent, enhanced_context)
            parsed_command.constraints = self._determine_constraints(parsed_command, enhanced_context)
            
            # Set priority
            parsed_command.priority = self._determine_priority(text, intent)
            
            # Validate command
            validated_command = await self.command_validator.validate_command(
                parsed_command, enhanced_context
            )
            
            # Update statistics
            parse_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_parser_stats(parse_time, validated_command.is_valid)
            
            logger.debug(f"Parsed command: {validated_command.intent.category.value if validated_command.intent else 'unknown'} "
                        f"({validated_command.intent.confidence if validated_command.intent else 0:.2f} confidence)")
            
            return validated_command
            
        except Exception as e:
            # Create error command
            error_command = ParsedCommand(
                original_text=text,
                normalized_text=text,
                validation_errors=[f"Parse error: {str(e)}"],
                suggestions=["Try rephrasing your command", "Check command syntax"]
            )
            
            # Update stats
            parse_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_parser_stats(parse_time, False)
            
            logger.error(f"Command parsing failed: {str(e)}")
            return error_command
    
    async def create_execution_plan(
        self,
        command: ParsedCommand,
        context: CommandContext,
        available_agents: Optional[List['BuiltAgent']] = None,
        available_tools: Optional[List[str]] = None
    ) -> ExecutionPlan:
        """Create execution plan for parsed command."""
        
        try:
            plan = ExecutionPlan(command_id=command.id)
            
            # Determine required capabilities
            required_capabilities = self._determine_required_capabilities(command)
            
            # Match agents and tools
            if available_agents:
                matched_agents = self._match_agents_to_capabilities(
                    available_agents, required_capabilities
                )
                plan.agents_required = [agent.id for agent in matched_agents]
            
            if available_tools:
                matched_tools = self._match_tools_to_capabilities(
                    available_tools, required_capabilities
                )
                plan.tools_required = matched_tools
            
            # Create execution steps
            plan.steps = await self._create_execution_steps(command, context)
            
            # Calculate estimates
            plan.estimated_duration = self._estimate_execution_duration(command, plan.steps)
            plan.complexity_score = context.metadata.get('command_complexity', 0.5)
            
            # Determine resource requirements
            plan.resource_requirements = self._determine_resource_requirements(command, plan)
            
            # Create fallback plans
            plan.fallback_plans = await self._create_fallback_plans(command, plan)
            
            logger.debug(f"Created execution plan for {command.id}: "
                        f"{len(plan.steps)} steps, {plan.estimated_duration:.1f}s estimated")
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create execution plan: {str(e)}")
            
            # Return minimal plan
            return ExecutionPlan(
                command_id=command.id,
                steps=[{'type': 'error', 'message': str(e)}],
                estimated_duration=0.0,
                complexity_score=1.0
            )
    
    def get_parser_statistics(self) -> Dict[str, Any]:
        """Get parser performance statistics."""
        return {
            'parser_stats': self.parser_stats,
            'supported_intents': [intent.value for intent in self.intent_recognizer.get_supported_intents()],
            'cache_size': len(self._pattern_cache),
            'uptime': datetime.utcnow().isoformat()
        }
    
    # === Private Helper Methods ===
    
    def _normalize_text(self, text: str) -> str:
        """Normalize input text for processing."""
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', text.strip())
        
        # Expand common contractions
        contractions = {
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
            "isn't": "is not",
            "aren't": "are not",
            "haven't": "have not",
            "hasn't": "has not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "shouldn't": "should not"
        }
        
        for contraction, expansion in contractions.items():
            normalized = normalized.replace(contraction, expansion)
            normalized = normalized.replace(contraction.title(), expansion.title())
        
        return normalized
    
    def _map_intent_to_command_type(self, intent: CommandIntent) -> CommandType:
        """Map intent category to command type."""
        mapping = {
            IntentCategory.ANALYZE: CommandType.ANALYSIS,
            IntentCategory.GENERATE: CommandType.GENERATION,
            IntentCategory.TRANSFORM: CommandType.TRANSFORMATION,
            IntentCategory.VALIDATE: CommandType.VALIDATION,
            IntentCategory.EXECUTE: CommandType.EXECUTION,
            IntentCategory.COORDINATE: CommandType.COORDINATION,
            IntentCategory.QUERY: CommandType.QUERY,
            IntentCategory.CONTROL: CommandType.CONTROL,
            IntentCategory.CREATE: CommandType.GENERATION,
            IntentCategory.READ: CommandType.QUERY,
            IntentCategory.UPDATE: CommandType.TRANSFORMATION,
            IntentCategory.DELETE: CommandType.CONTROL
        }
        
        return mapping.get(intent.category, CommandType.QUERY)
    
    async def _extract_parameters(
        self,
        text: str,
        intent: CommandIntent,
        context: CommandContext
    ) -> Dict[str, Any]:
        """Extract parameters from command text and intent."""
        
        parameters = intent.parameters.copy()
        
        # Extract common parameter patterns
        parameter_patterns = {
            'format': r'\b(?:format|type|as|to)\s+(\w+)\b',
            'output': r'\b(?:output|save|write)\s+(?:to\s+)?([^\s]+)',
            'input': r'\b(?:input|from|using)\s+([^\s]+)',
            'count': r'\b(?:number|count|limit)\s+(?:of\s+)?(\d+)',
            'timeout': r'\b(?:timeout|wait|within)\s+(\d+)\s*(?:seconds?|minutes?|hours?)?',
            'priority': r'\b(?:priority|urgent|high|low|normal)\b'
        }
        
        for param_name, pattern in parameter_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parameters[param_name] = match.group(1)
        
        # Extract variables from context
        if context.variables:
            for var_name, var_value in context.variables.items():
                if var_name.endswith('_found') and var_value:
                    clean_name = var_name.replace('_found', '')
                    parameters[clean_name] = var_value
        
        return parameters
    
    def _determine_requirements(
        self,
        intent: CommandIntent,
        context: CommandContext
    ) -> List[str]:
        """Determine context requirements for command."""
        
        requirements = []
        
        # Intent-based requirements
        if intent.category in [IntentCategory.COORDINATE]:
            requirements.append('team')
        elif intent.category in [IntentCategory.EXECUTE, IntentCategory.CONTROL]:
            requirements.append('agent')
        
        # Target-based requirements
        if intent.target:
            if 'project' in intent.target.lower():
                requirements.append('project')
            elif 'workflow' in intent.target.lower():
                requirements.append('workflow')
        
        # Context-based requirements
        if context.scope == ContextScope.PROJECT:
            requirements.append('project')
        elif context.scope == ContextScope.WORKFLOW:
            requirements.append('workflow')
        elif context.scope == ContextScope.TEAM:
            requirements.append('team')
        elif context.scope == ContextScope.AGENT:
            requirements.append('agent')
        
        return list(set(requirements))  # Remove duplicates
    
    def _determine_constraints(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Dict[str, Any]:
        """Determine execution constraints for command."""
        
        constraints = {}
        
        # Time constraints
        if 'urgent' in command.original_text.lower():
            constraints['max_duration'] = 60  # 1 minute
        elif 'quick' in command.original_text.lower():
            constraints['max_duration'] = 300  # 5 minutes
        
        # Resource constraints
        if context.metadata.get('command_complexity', 0) > 0.8:
            constraints['requires_high_capability_agent'] = True
        
        # Scope constraints
        if context.scope != ContextScope.GLOBAL:
            constraints['scope_limited'] = True
            constraints['allowed_scope'] = context.scope.value
        
        return constraints
    
    def _determine_priority(self, text: str, intent: CommandIntent) -> CommandPriority:
        """Determine command execution priority."""
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['urgent', 'critical', 'emergency', 'asap']):
            return CommandPriority.CRITICAL
        elif any(keyword in text_lower for keyword in ['high', 'important', 'priority']):
            return CommandPriority.HIGH
        elif any(keyword in text_lower for keyword in ['low', 'background', 'when you have time']):
            return CommandPriority.LOW
        elif any(keyword in text_lower for keyword in ['later', 'eventually', 'sometime']):
            return CommandPriority.BACKGROUND
        else:
            return CommandPriority.NORMAL
    
    def _determine_required_capabilities(self, command: ParsedCommand) -> List[str]:
        """Determine required capabilities for command execution."""
        
        capabilities = []
        
        # Command type capabilities
        type_capabilities = {
            CommandType.ANALYSIS: ['analysis', 'code_understanding', 'pattern_recognition'],
            CommandType.GENERATION: ['generation', 'creative_writing', 'code_generation'],
            CommandType.TRANSFORMATION: ['transformation', 'format_conversion', 'data_processing'],
            CommandType.VALIDATION: ['validation', 'testing', 'quality_assurance'],
            CommandType.EXECUTION: ['execution', 'automation', 'process_management'],
            CommandType.COORDINATION: ['coordination', 'team_management', 'workflow_orchestration'],
            CommandType.QUERY: ['search', 'information_retrieval', 'knowledge_base'],
            CommandType.CONTROL: ['control', 'process_management', 'system_administration']
        }
        
        if command.command_type:
            capabilities.extend(type_capabilities.get(command.command_type, []))
        
        # Parameter-based capabilities
        if 'code' in str(command.parameters):
            capabilities.append('code_understanding')
        if 'test' in str(command.parameters):
            capabilities.append('testing')
        if 'documentation' in str(command.parameters):
            capabilities.append('documentation')
        
        return list(set(capabilities))
    
    def _match_agents_to_capabilities(
        self,
        agents: List['BuiltAgent'],
        capabilities: List[str]
    ) -> List['BuiltAgent']:
        """Match agents to required capabilities."""
        
        matched_agents = []
        
        for agent in agents:
            # In a real implementation, agents would have capability metadata
            # For now, assume all agents can handle basic capabilities
            agent_capabilities = getattr(agent, 'capabilities', ['general'])
            
            if any(cap in agent_capabilities for cap in capabilities) or 'general' in agent_capabilities:
                matched_agents.append(agent)
        
        return matched_agents[:3]  # Limit to top 3 matches
    
    def _match_tools_to_capabilities(
        self,
        tools: List[str],
        capabilities: List[str]
    ) -> List[str]:
        """Match tools to required capabilities."""
        
        # Tool capability mapping (simplified)
        tool_capabilities = {
            'code_analyzer': ['analysis', 'code_understanding'],
            'test_runner': ['testing', 'validation'],
            'documentation_generator': ['documentation', 'generation'],
            'workflow_executor': ['execution', 'workflow_orchestration'],
            'data_transformer': ['transformation', 'data_processing']
        }
        
        matched_tools = []
        for tool in tools:
            tool_caps = tool_capabilities.get(tool, [])
            if any(cap in tool_caps for cap in capabilities):
                matched_tools.append(tool)
        
        return matched_tools
    
    async def _create_execution_steps(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> List[Dict[str, Any]]:
        """Create detailed execution steps for command."""
        
        steps = []
        
        # Basic step structure based on command type
        if command.command_type == CommandType.ANALYSIS:
            steps = [
                {'type': 'preparation', 'action': 'gather_input_data', 'description': 'Collect data to analyze'},
                {'type': 'analysis', 'action': 'perform_analysis', 'description': 'Execute analysis logic'},
                {'type': 'presentation', 'action': 'format_results', 'description': 'Format and present results'}
            ]
        elif command.command_type == CommandType.GENERATION:
            steps = [
                {'type': 'planning', 'action': 'create_generation_plan', 'description': 'Plan what to generate'},
                {'type': 'generation', 'action': 'generate_content', 'description': 'Generate requested content'},
                {'type': 'validation', 'action': 'validate_output', 'description': 'Validate generated content'},
                {'type': 'delivery', 'action': 'deliver_results', 'description': 'Deliver final results'}
            ]
        elif command.command_type == CommandType.EXECUTION:
            steps = [
                {'type': 'preparation', 'action': 'prepare_execution_environment', 'description': 'Set up execution environment'},
                {'type': 'execution', 'action': 'execute_command', 'description': 'Execute the specified command'},
                {'type': 'monitoring', 'action': 'monitor_execution', 'description': 'Monitor execution progress'},
                {'type': 'cleanup', 'action': 'cleanup_environment', 'description': 'Clean up after execution'}
            ]
        else:
            # Generic steps
            steps = [
                {'type': 'preparation', 'action': 'prepare', 'description': 'Prepare for command execution'},
                {'type': 'execution', 'action': 'execute', 'description': 'Execute main command logic'},
                {'type': 'finalization', 'action': 'finalize', 'description': 'Finalize and report results'}
            ]
        
        # Add step IDs and estimated durations
        for i, step in enumerate(steps):
            step['id'] = f"step_{i+1}"
            step['estimated_duration'] = 10.0 + (i * 5.0)  # Simple duration estimation
            step['parameters'] = json.dumps(command.parameters)
        
        return steps
    
    def _estimate_execution_duration(
        self,
        command: ParsedCommand,
        steps: List[Dict[str, Any]]
    ) -> float:
        """Estimate total execution duration."""
        
        base_duration = sum(step.get('estimated_duration', 10.0) for step in steps)
        
        # Adjust based on complexity
        complexity_multiplier = 1.0 + (command.constraints.get('command_complexity', 0.5) * 2.0)
        
        # Adjust based on priority (higher priority might get more resources)
        priority_multiplier = {
            CommandPriority.CRITICAL: 0.5,
            CommandPriority.HIGH: 0.7,
            CommandPriority.NORMAL: 1.0,
            CommandPriority.LOW: 1.5,
            CommandPriority.BACKGROUND: 2.0
        }.get(command.priority, 1.0)
        
        return base_duration * complexity_multiplier * priority_multiplier
    
    def _determine_resource_requirements(
        self,
        command: ParsedCommand,
        plan: ExecutionPlan
    ) -> Dict[str, Any]:
        """Determine resource requirements for execution."""
        
        requirements = {
            'cpu_intensive': command.command_type in [CommandType.ANALYSIS, CommandType.GENERATION],
            'memory_intensive': len(str(command.parameters)) > 1000,
            'network_required': 'url' in str(command.parameters) or 'api' in str(command.parameters),
            'storage_required': 'file' in str(command.parameters) or 'save' in str(command.parameters),
            'agent_count': len(plan.agents_required),
            'tool_count': len(plan.tools_required),
            'parallel_execution': len([s for s in plan.steps if s.get('type') == 'execution']) > 1
        }
        
        return requirements
    
    async def _create_fallback_plans(
        self,
        command: ParsedCommand,
        primary_plan: ExecutionPlan
    ) -> List[Dict[str, Any]]:
        """Create fallback plans for error recovery."""
        
        fallbacks = []
        
        # Simplified fallback - retry with different agents
        if len(primary_plan.agents_required) > 1:
            fallbacks.append({
                'type': 'agent_fallback',
                'description': 'Retry with alternative agents',
                'agents': primary_plan.agents_required[1:],  # Use different agents
                'estimated_duration': primary_plan.estimated_duration * 1.2
            })
        
        # Simplified fallback - reduce complexity
        if primary_plan.complexity_score > 0.7:
            fallbacks.append({
                'type': 'complexity_reduction',
                'description': 'Simplify command and retry',
                'modifications': ['reduce_scope', 'remove_optional_parameters'],
                'estimated_duration': primary_plan.estimated_duration * 0.8
            })
        
        # Manual intervention fallback
        fallbacks.append({
            'type': 'manual_intervention',
            'description': 'Request human assistance',
            'escalation': True,
            'estimated_duration': 0.0  # Indefinite
        })
        
        return fallbacks
    
    def _update_parser_stats(self, parse_time: float, success: bool) -> None:
        """Update parser performance statistics."""
        
        self.parser_stats['total_commands_parsed'] += 1
        
        if success:
            self.parser_stats['successful_parses'] += 1
        else:
            self.parser_stats['failed_parses'] += 1
        
        # Update average parse time
        total_parses = self.parser_stats['total_commands_parsed']
        current_avg = self.parser_stats['average_parse_time']
        
        self.parser_stats['average_parse_time'] = (
            (current_avg * (total_parses - 1) + parse_time) / total_parses
        )
        
        # Calculate intent accuracy (simplified)
        if total_parses > 0:
            self.parser_stats['intent_accuracy'] = (
                self.parser_stats['successful_parses'] / total_parses
            )


# === FACTORY FUNCTION ===

def create_protocol_parser(
    intent_recognizer: Optional[IntentRecognizer] = None
) -> ProtocolParser:
    """Create ProtocolParser with default dependencies."""
    return ProtocolParser(intent_recognizer=intent_recognizer)


# === EXAMPLE USAGE ===

async def example_protocol_parser_usage():
    """Example usage of ProtocolParser."""
    
    # Create parser
    parser = create_protocol_parser()
    
    # Example commands
    test_commands = [
        "Analyze the code in main.py for potential issues",
        "Generate unit tests for the UserService class",
        "Transform JSON data to CSV format",
        "Execute the deployment workflow",
        "Coordinate the development team for sprint planning",
        "Search for all functions that use the deprecated API"
    ]
    
    # Parse commands
    for command_text in test_commands:
        print(f"\n--- Parsing: '{command_text}' ---")
        
        # Create context
        context = CommandContext(
            user_id="test_user",
            session_id="test_session",
            project_id="test_project"
        )
        
        # Parse command
        parsed = await parser.parse_command(command_text, context)
        
        print(f"Intent: {parsed.intent.category.value if parsed.intent else 'unknown'}")
        print(f"Confidence: {parsed.intent.confidence if parsed.intent else 0:.2f}")
        print(f"Command Type: {parsed.command_type.value if parsed.command_type else 'unknown'}")
        print(f"Valid: {parsed.is_valid}")
        print(f"Parameters: {parsed.parameters}")
        
        if parsed.validation_errors:
            print(f"Errors: {parsed.validation_errors}")
        if parsed.suggestions:
            print(f"Suggestions: {parsed.suggestions}")
        
        # Create execution plan
        if parsed.is_valid:
            plan = await parser.create_execution_plan(parsed, context)
            print(f"Execution Plan: {len(plan.steps)} steps, {plan.estimated_duration:.1f}s estimated")
    
    # Show parser statistics
    stats = parser.get_parser_statistics()
    print(f"\n--- Parser Statistics ---")
    print(json.dumps(stats, indent=2, default=str))


if __name__ == "__main__":
    # Run example usage
    import asyncio
    asyncio.run(example_protocol_parser_usage())
