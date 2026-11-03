"""Fabrique des objets d'exécution (portage de ``WorkflowFactory``).

Différence assumée avec le source (bug §5 non reproduit) :
``CreateBaseIncomingEvent`` inversait le test sur le type nommé — le chemin
« type enregistré » levait une ``NullReferenceException``. Ici, un type
nommé est résolu dans le registre des créateurs, et son absence lève une
``LookupError`` claire (enveloppée par le moteur).
"""

from __future__ import annotations

import copy
from typing import Any, Callable, Dict, Mapping, Optional, Tuple, Union

from ..clock import WorkflowClock
from ..models import ChangeEnum, Event, IncomingEvent, RunContext, Workflow, new_uuid
from .serializer import populate_incoming_event


class WorkflowFactory:
    """Crée workflows, événements et contextes d'exécution.

    ``context_factory`` permet d'utiliser une sous-classe de
    :class:`RunContext` (l'équivalent du ``TContext`` générique du source) ;
    ``context_initializer`` est appelé sur chaque contexte créé.
    """

    def __init__(
        self,
        new_incoming_event: Optional[Callable[[], IncomingEvent]] = None,
        new_workflow: Optional[Callable[[], Workflow]] = None,
        *,
        context_factory: Callable[[], RunContext] = RunContext,
        context_initializer: Optional[Callable[[RunContext], None]] = None,
    ) -> None:
        self._default_incoming_event = new_incoming_event or IncomingEvent
        self._default_workflow = new_workflow or Workflow
        self._incoming_event_creators: Dict[str, Callable[[], IncomingEvent]] = {}
        self._workflow_creators: Dict[Tuple[str, int], Callable[[], Workflow]] = {}
        self.context_factory = context_factory
        self.context_initializer = context_initializer

    # ------------------------------------------------------------------
    # Enregistrement (API fluide, comme le source)
    # ------------------------------------------------------------------

    def add_incoming_event(
        self, key: str, creator: Callable[[], IncomingEvent]
    ) -> "WorkflowFactory":
        self._incoming_event_creators[key] = creator
        return self

    def add_workflow(
        self, workflow_name: str, version: int, creator: Callable[[], Workflow]
    ) -> "WorkflowFactory":
        self._workflow_creators[(workflow_name, version)] = creator
        return self

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------

    def create_base_incoming_event(
        self,
        payload: Union[str, Mapping[str, Any], IncomingEvent],
        incoming_type: Optional[str] = None,
    ) -> IncomingEvent:
        """Désérialise un payload en événement entrant.

        Un :class:`IncomingEvent` déjà construit est retourné tel quel.
        """
        if isinstance(payload, IncomingEvent):
            return payload

        if incoming_type:
            creator = self._incoming_event_creators.get(incoming_type)
            if creator is None:
                raise LookupError(
                    f"no incoming event registered for type {incoming_type!r}"
                )
        else:
            creator = self._default_incoming_event

        return populate_incoming_event(creator(), payload)

    def create_new_workflow(
        self,
        workflow_name: str,
        workflow_version: int,
        external_id: str,
        extended_datas: Optional[Mapping[str, Any]] = None,
    ) -> Workflow:
        workflow = self._get_workflow(workflow_name, workflow_version)

        workflow.uuid = new_uuid()
        workflow.workflow_name = workflow_name
        workflow.version = workflow_version
        workflow.external_id = external_id
        workflow.creation_date = WorkflowClock.now()
        workflow.last_update_date = WorkflowClock.now()
        workflow.concurrency = 1
        workflow.change = ChangeEnum.NEW

        if extended_datas:
            workflow.extended_datas.update(copy.deepcopy(dict(extended_datas)))

        return workflow

    def create_base_event(self, incoming_event: IncomingEvent) -> Event:
        # L'événement d'historique porte l'uuid de l'événement entrant :
        # c'est ce qui rend opérante la garde « un événement ne peut pas
        # être intégré deux fois ». Le source générait un Guid neuf, et sa
        # garde ne pouvait donc jamais se déclencher (bug non reproduit).
        return Event(
            uuid=incoming_event.uuid,
            name=incoming_event.name,
            event_date=incoming_event.event_date,
            creation_date=WorkflowClock.now(),
            change=ChangeEnum.NEW,
            extended_datas=copy.deepcopy(incoming_event.extended_datas),
        )

    def create_context(
        self, workflow: Workflow, incoming_event: IncomingEvent
    ) -> RunContext:
        context = self.context_factory()
        context.workflow = workflow
        context.incoming_event = incoming_event
        context.event = self.create_base_event(incoming_event)

        if self.context_initializer is not None:
            self.context_initializer(context)

        return context

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _get_workflow(self, workflow_name: str, version: int) -> Workflow:
        creator = self._workflow_creators.get((workflow_name, version))
        if creator is None:
            creator = self._default_workflow
        return creator()
