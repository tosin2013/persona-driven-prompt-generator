# Project Plan: Persona-Driven Prompt Generator Cleanup

## Current State
- Multiple versions of main files exist (`main.py`, `main_temp.py`)
- Recent changes made to `persona_management.py` and `llm_interaction.py`
- Potential backup files and temporary files may exist

## Changes Made
1. **Persona Management Updates**
   - Enhanced persona generation with human-like names
   - Improved LLM prompt for more realistic persona generation
   - Added better error handling and JSON parsing

2. **AutoGen Integration**
   - Added workflow type selection (Autonomous/Sequential)
   - Added agent type configuration
   - Updated workflow generation to use personas
   - Changed workflow output from JSON to Python code

3. **UI Improvements**
   - Added markdown export functionality
   - Improved persona display
   - Added configuration options in sidebar

## Cleanup Tasks
1. **File Cleanup**
   - [ ] Create backup directory
   - [ ] Move all backup/temp files to backup directory
   - [ ] Remove unnecessary files
   - [ ] Update .gitignore to exclude backup directory

2. **Code Consolidation**
   - [ ] Verify `main.py` has all latest changes
   - [ ] Remove `main_temp.py` after verification
   - [ ] Update any import references in other files

3. **Documentation Update**
   - [ ] Update README.md with new features
   - [ ] Document AutoGen configuration options
   - [ ] Add examples of different workflow types
   - [ ] Document persona generation capabilities

4. **Testing**
   - [ ] Test persona generation with different counts
   - [ ] Test both AutoGen workflow types
   - [ ] Test markdown export functionality
   - [ ] Verify all UI components work correctly

## Files to Keep
- `main.py` (Latest version)
- `persona_management.py` (Updated)
- `llm_interaction.py` (Updated)
- `utils.py`
- `database.py`
- `search.py`
- `config.py`
- All test files
- Documentation files (README.md, etc.)

## Files to Archive/Remove
- `main_temp.py`
- Any `.py.backup` files
- Generated workflow files
- Temporary test files

## Post-Cleanup Verification
1. **Functionality Check**
   - [ ] Persona generation works with human names
   - [ ] AutoGen workflow generation works
   - [ ] UI displays correctly
   - [ ] Export functions work

2. **Code Quality**
   - [ ] No duplicate code between files
   - [ ] All imports resolve correctly
   - [ ] No unused functions
   - [ ] Consistent code style

## Next Steps
1. Execute cleanup tasks in order
2. Test after each major change
3. Document any issues encountered
4. Update documentation with final state
5. Create new backup of cleaned codebase

## Notes
- Keep track of any files modified during cleanup
- Document any configuration changes needed
- Note any dependencies that need to be updated
- Maintain test coverage during cleanup
