"""Noms techniques du moteur (événements et actions réservés).

Portage de ``Bb.Workflows.Constants`` — les valeurs sont conservées à
l'identique pour rester compatible avec les configurations existantes.
"""

CURRENT_WORKFLOW = "_workflow"

SET_VALUE_ACTION_NAME = "$_update"
PUSH_ACTION_NAME = "$_push"
PUSH_REMINDER = "$_reminder"

EVENT_ID = "EventId"
TASK_UUID = "TaskId"

# Événements techniques
RESULT_ACTION_NAME = "$_result"
EXPIRED_EVENT_NAME = "__expired"
CANCEL_REMINDER_ACTION = "__cancelReminderAction"

# Propriétés réservées des données étendues
WORKFLOW_ID_PROPERTY = "WorkflowId"
