# Project Overview

## Goal
SkipTLU automates and verifies learning progress on Moodle/ELMS, initially targeting ELMS-TLU.

## Scope
- Discover course/section/activity.
- Identify Moodle module type.
- Resolve completion requirements.
- Route to module-specific handler.
- Execute the minimum valid workflow.
- Re-read server state and report the result.

## Design rule
Activity IDs discovered during analysis are test data only. Production discovery must be dynamic; no hard-coded IDs.
