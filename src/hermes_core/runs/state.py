NEW_PROJECT_STATES = {
    "received",
    "triaged",
    "manager_policy_checked",
    "larv_full_session_started",
    "larv_full_waiting_for_input",
    "larv_full_input_received",
    "larv_full_resumed",
    "larv_full_completed",
    "larv_full_interrupted",
    "larv_full_recovery_required",
    "larv_artifacts_ingested",
    "project_context_candidate_created",
    "worker_execution_running",
    "qa_verification_running",
    "final_report_ready",
    "permanent_project_agent_created",
    "learning_candidates_created",
    "completed",
    "failed",
}

ISSUE_FIX_STATES = {
    "received",
    "triaged",
    "mad_confidence_scored",
    "solo_or_assembly_selected",
    "context_oracle_analysis_done",
    "implementation_running",
    "qa_verification_running",
    "project_agent_review_done",
    "manager_audit_done",
    "final_report_ready",
    "awaiting_human_pr_approval",
    "learning_candidates_created",
    "completed",
    "failed",
}

WORKFLOW_STATES = {
    "new_project_creation": NEW_PROJECT_STATES,
    "issue_fix": ISSUE_FIX_STATES,
}

