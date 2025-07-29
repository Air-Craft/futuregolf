# Development Agent Spec

For reaonsably self-contained features spawn an agent and obey the following instructions. 

IMPORTANT: If Node will be utilised, first check that `nvm list` works. If not, then we have an environment error. Abort and notify.

For working on an independent feature, do the following:

* First read OVERVIEW.md and all relevant sub specs in the Spec/ folder and subfolders.
* Git clone from the primary repository (ask the user if not found in Spec/OVERVIEW.md) in to a "repo/" subfolder. Make that your working directory.
* Create a dedicated git branch prefixed with the name "feature/"
* Create a folder with the same name `[test_folder]/feature/my-feature` in the relevant test subfolder (backend/tests/, iOS/FutureGolfTests, etc.)
* Write the test stubbs that will indicate the feature is complete. Make sure they fail if not implemented.
* Write the code for the feature and the tests.
* Create/Update docs here in the Dev/ folder to reflect the new feature, and make any changes Spec/ docs if we've changed something (e.g. changed OpenAI Whisper to ElevenLabs)
* Commit, push and issue a Pull Request via the CLI. 
* Fix and failed tests and push again. Continue until all errors are fixed.
* But if you are stuck on fixing an error for more than 7 iterations, then stop and report what you have tried and the final result.
* Follow Spec docs precisely and making intelligent, and style-aware improvisation when needed. 
* If you are unsure of how to proceed, then ask, cancelling the operation if need be.

