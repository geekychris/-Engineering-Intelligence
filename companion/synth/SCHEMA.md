# Output schema

Every stream is emitted as JSON Lines: one JSON object per line, sorted
keys, no trailing whitespace. Timestamps are UTC epoch seconds so no
timezone context is needed to interpret them.

## teams.jsonl

| field  | type   | note                                    |
| ------ | ------ | --------------------------------------- |
| id     | string | `team_NNN`                              |
| name   | string | display name drawn from a curated pool  |
| domain | string | one of a fixed list of business domains |

## actors.jsonl

| field        | type   | note                                          |
| ------------ | ------ | --------------------------------------------- |
| id           | string | `actor_NNNNN`                                 |
| kind         | string | `human`, `bot`, or `agent`                    |
| display_name | string | representative name (invented)                |
| team_id      | string | FK to `teams.id`                              |
| role         | string | `engineer`, `specialist`, `ci-bot`, `agent`   |
| scarcity     | float  | 1.0 = plentiful; ≥ 2.4 for specialists        |

## services.jsonl

| field           | type    | note                                    |
| --------------- | ------- | --------------------------------------- |
| id              | string  | `svc_NNNN`                              |
| team_id         | string  | FK to `teams.id`                        |
| name            | string  | `<team>-<n>`                            |
| fanout          | integer | rough downstream-dependency count       |
| customer_facing | boolean | true for internet-facing services       |

## pull_requests.jsonl

Event log; one row per lifecycle event.

| event                            | additional fields                         |
| -------------------------------- | ----------------------------------------- |
| `pull_request.opened`            | `pr_id`, `author_id`, `service_id`, `team_id` |
| `pull_request.review_requested`  | `pr_id`, `reviewer_id`                    |
| `pull_request.review_submitted`  | `pr_id`, `reviewer_id`, `state`           |
| `pull_request.merged`            | `pr_id`                                   |
| `pull_request.closed`            | `pr_id`                                   |

Every row also carries `event` and `at` (epoch seconds).

## ci_runs.jsonl

| event                | additional fields                             |
| -------------------- | --------------------------------------------- |
| `ci.run.started`     | `run_id`, `pr_id`                             |
| `ci.run.finished`    | `run_id`, `pr_id`, `outcome`                  |

`outcome` is `passed` or `failed`.

## deployments.jsonl

| event                    | additional fields                             |
| ------------------------ | --------------------------------------------- |
| `deployment.started`     | `deployment_id`, `pr_id`, `service_id`, `environment` |
| `deployment.finished`    | `deployment_id`, `outcome`                    |

## incidents.jsonl

| event                | additional fields                                        |
| -------------------- | -------------------------------------------------------- |
| `incident.declared`  | `incident_id`, `severity`, `service_id`, `linked_deployment_id` |
| `incident.mitigated` | `incident_id`                                            |

`severity` is `sev1` (worst) through `sev4`.

## engineering_changes.jsonl

Grouped-work records — one row per reconstructed Engineering Change.

| field                        | type    | note                                                   |
| ---------------------------- | ------- | ------------------------------------------------------ |
| engineering_change_id        | string  | `ec_NNNNNN`                                            |
| author_id                    | string  | FK to `actors.id`                                      |
| pr_ids                       | list    | pull requests that comprise this change                 |
| reconstruction_confidence    | float   | 0-1; lower for multi-PR groupings inferred heuristically |
| opened_at                    | integer | epoch seconds of the earliest PR in the group           |
