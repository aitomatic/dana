# Prompt
- I want you to read and understand the content of `dana_studio/dana/studio/api/routers/v2/knowledge_pack/kp_interview_session.py`, focus on `session_chat`. This API   will be served  
  in the UI with these components : left side is the chat box and right side will show the progression. At the moment, i receive the following feedback from the end user `[Pasted      
  text #2 +86 lines]`. Read the files and its lower level component to understand the logic, then list out some potential causes the the above problems 

# Interview template issues
---                                                                                                                                                                                   
  Potential Root Causes for Template Editing Issues                                                                                                                                     
                                                                                                                                                                                        
  1. Conversation History Truncation (Major)                                                                                                                                            
                                                                                                                                                                                        
  Location: template_modification_handler.py:86-97                                                                                                                                      
                                                                                                                                                                                        
  conversation = []                                                                                                                                                                     
  is_in_editor_mode = False                                                                                                                                                             
  for message in raw_conversation[::-1]:                                                                                                                                                
      if message.metadata.get("mode") == "editor":                                                                                                                                      
          is_in_editor_mode = True                                                                                                                                                      
          continue                                                                                                                                                                      
      elif message.metadata.get("mode") == "auto" and is_in_editor_mode:                                                                                                                
          is_in_editor_mode = False                                                                                                                                                     
          continue                                                                                                                                                                      
      conversation.append(message)                                                                                                                                                      
      if len(conversation) >= 10:                                                                                                                                                       
          break                                                                                                                                                                         
                                                                                                                                                                                        
  Problem: Only uses the last 10 messages and filters by mode. When users iterate on a template over many turns, earlier context (like the original desired content or "keep everything 
  else the same" instructions) gets lost.                                                                                                                                               
                                                                                                                                                                                        
  Also in: document_exploration_handler.py:107-108 (only 4 messages!)                                                                                                                   
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  2. Mode Detection Non-Determinism (Major)                                                                                                                                             
                                                                                                                                                                                        
  Location: kp_interview_template.py:650-724                                                                                                                                            
                                                                                                                                                                                        
  async def detect_chat_mode(                                                                                                                                                           
      user_message: str,                                                                                                                                                                
      chat_history: list[MessageData] | None = None,                                                                                                                                    
      ...                                                                                                                                                                               
  ) -> str:                                                                                                                                                                             
      # Uses LLM to detect mode - introduces uncertainty                                                                                                                                
      # Only considers last 6 messages                                                                                                                                                  
      recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history                                                                                                     
                                                                                                                                                                                        
  Problem:                                                                                                                                                                              
  - LLM-based mode detection is non-deterministic                                                                                                                                       
  - The mode affects which handler runs (EDITOR vs CHAT)                                                                                                                                
  - Mode metadata is stored per-message and used for previous_mode tracking                                                                                                             
  - A single misclassification can cause unexpected behavior changes (the "checkbox" UI symptom)                                                                                        
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  3. No Atomic Template Updates (Major)                                                                                                                                                 
                                                                                                                                                                                        
  Location: replace_in_file_tool.py:162-233                                                                                                                                             
                                                                                                                                                                                        
  def _apply_diff(self, content: str, diff: str) -> tuple[str, int]:                                                                                                                    
      for block in blocks:                                                                                                                                                              
          occurrences = new_content.count(search_content)                                                                                                                               
          if occurrences > 1:                                                                                                                                                           
              # Multiple matches - skip this block, add to suggestions                                                                                                                  
              suggestions.append(suggestion)                                                                                                                                            
              continue  # Other blocks may still apply!                                                                                                                                 
          if occurrences == 1:                                                                                                                                                          
              # Apply change                                                                                                                                                            
              new_content = new_content.replace(...)                                                                                                                                    
                                                                                                                                                                                        
  Problem:                                                                                                                                                                              
  - If one SEARCH/REPLACE block fails (ambiguous or not found), others may still apply                                                                                                  
  - Partial updates leave template in inconsistent state                                                                                                                                
  - No rollback mechanism                                                                                                                                                               
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  4. Stale Content in LLM Context                                                                                                                                                       
                                                                                                                                                                                        
  Location: template_modification_handler.py:99-115                                                                                                                                     
                                                                                                                                                                                        
  # Check if view_template was already called                                                                                                                                           
  has_view_template = any("<view_template>" in msg.content for msg in conversation)                                                                                                     
                                                                                                                                                                                        
  if not has_view_template:                                                                                                                                                             
      # Execute view_template tool with default parameters                                                                                                                              
      tool_msg = await self._execute_tool(tool_name="view_template", params={"section": "all"}, ...)                                                                                    
                                                                                                                                                                                        
  Problem:                                                                                                                                                                              
  - Template is read once at the start of a handler session                                                                                                                             
  - If multiple turns occur without refreshing, LLM works with old content                                                                                                              
  - After a modification, the LLM's context still has the old view_template result                                                                                                      
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  5. Response Deduplication Logic                                                                                                                                                       
                                                                                                                                                                                        
  Location: kp_interview_template.py:934-951                                                                                                                                            
                                                                                                                                                                                        
  new_messages = []                                                                                                                                                                     
  for message in reversed(internal_conversation):                                                                                                                                       
      if (                                                                                                                                                                              
          conversation.messages                                                                                                                                                         
          and message.role == conversation.messages[-1].sender                                                                                                                          
          and message.content == conversation.messages[-1].content                                                                                                                      
      ):                                                                                                                                                                                
          break  # Stops adding messages if duplicate found                                                                                                                             
      new_messages.append(...)                                                                                                                                                          
                                                                                                                                                                                        
  Problem: This deduplication could incorrectly drop messages or truncate the conversation.                                                                                             
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  6. Template Diff Not Returned in All Cases                                                                                                                                            
                                                                                                                                                                                        
  Location: kp_interview_template.py:976-1043                                                                                                                                           
                                                                                                                                                                                        
  if template_modified:                                                                                                                                                                 
      # Only compute diff if template_modified is True                                                                                                                                  
      template_diff = ...                                                                                                                                                               
                                                                                                                                                                                        
  Problem:                                                                                                                                                                              
  - template_modified is set based on tool name check (tool_name == "replace_in_template")                                                                                              
  - If the tool runs but doesn't actually change anything (pattern not found), template_modified may still be True                                                                      
  - UI might not receive accurate diff information                                                                                                                                      
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  7. UI Sync Gap (Likely Frontend Issue)                                                                                                                                                
                                                                                                                                                                                        
  The API returns:                                                                                                                                                                      
  - template_modified: bool                                                                                                                                                             
  - template_diff: TemplateDiff | None                                                                                                                                                  
  - agent_response: str                                                                                                                                                                 
                                                                                                                                                                                        
  But the actual new template content is only sent via template_diff.new_content (when modified). If the UI doesn't properly consume this or relies on a separate GET endpoint that's   
  not called, the right pane becomes stale.                                                                                                                                             
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  8. Tool Result Role Assignment Confusion                                                                                                                                              
                                                                                                                                                                                        
  Location: template_modification_handler.py:248-253                                                                                                                                    
                                                                                                                                                                                        
  if result.require_user:                                                                                                                                                               
      role = SenderRole.ASSISTANT                                                                                                                                                       
  elif tool_name == "view_template":                                                                                                                                                    
      role = SenderRole.ASSISTANT                                                                                                                                                       
  else:                                                                                                                                                                                 
      role = SenderRole.USER  # Tool results appear as "user" messages                                                                                                                  
                                                                                                                                                                                        
  Problem: This affects how the LLM interprets the conversation - tool results appearing as user messages can confuse the model.                                                        
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  Summary of Fix Targets                                                                                                                                                                
  ┌───────────┬────────────────────────────────┬───────────────────────────────────────────────────┐                                                                                    
  │ Priority  │             Issue              │                   Fix Approach                    │                                                                                    
  ├───────────┼────────────────────────────────┼───────────────────────────────────────────────────┤                                                                                    
  │ 🔴 High   │ Conversation truncation        │ Increase limits; preserve critical instructions   │                                                                                    
  ├───────────┼────────────────────────────────┼───────────────────────────────────────────────────┤                                                                                    
  │ 🔴 High   │ Mode detection non-determinism │ Consider explicit mode selection in UI            │                                                                                    
  ├───────────┼────────────────────────────────┼───────────────────────────────────────────────────┤                                                                                    
  │ 🔴 High   │ Partial updates on failures    │ Make batched replacements atomic (all-or-nothing) │                                                                                    
  ├───────────┼────────────────────────────────┼───────────────────────────────────────────────────┤                                                                                    
  │ 🟡 Medium │ Stale template in context      │ Re-read template after each modification          │                                                                                    
  ├───────────┼────────────────────────────────┼───────────────────────────────────────────────────┤                                                                                    
  │ 🟡 Medium │ UI sync gap                    │ Always return new_content in response             │                                                                                    
  ├───────────┼────────────────────────────────┼───────────────────────────────────────────────────┤                                                                                    
  │ 🟠 Lower  │ Role assignment                │ Standardize tool result roles                     │                                                                                    
  └───────────┴────────────────────────────────┴───────────────────────────────────────────────────┘                                                                                    
  Would you like me to explore any of these issues in more detail or propose specific code changes? 

# Interview session issues

⏺ Prioritized Issues by Critical Level                                                                                                                                                  
                                                                                                                                                                                        
  🔴 CRITICAL (P0) - Follow-Up Limiter Not Enforced                                                                                                                                     
                                                                                                                                                                                        
  Impact: Major blocker - directly causes the "rabbit hole" problem                                                                                                                     
  - Occurred 3 times in a single 57-minute session                                                                                                                                      
  - System asked 6-8+ follow-ups instead of max 2                                                                                                                                       
  - Root cause: No counter exists at orchestration layer - entirely reliant on LLM judgment                                                                                             
  - Fix complexity: Medium - requires adding counter logic to session_chat                                                                                                              
                                                                                                                                                                                        
  Why P0: This is the core issue. Without a hard limit, the other issues cascade from it.                                                                                               
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  🟠 HIGH (P1) - "Move On" Command Unreliable                                                                                                                                           
                                                                                                                                                                                        
  Impact: User cannot escape rabbit holes even when explicitly requesting                                                                                                               
  - Required multiple attempts to work                                                                                                                                                  
  - Sometimes didn't work at all                                                                                                                                                        
  - Root cause: No explicit "move on" intent handler in prompts                                                                                                                         
  - Fix complexity: Low-Medium - add intent pattern + force topic transition logic                                                                                                      
                                                                                                                                                                                        
  Why P1: This is the escape valve. Even if follow-ups exceed limit, user should be able to manually escape. Currently broken.                                                          
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  🟡 MEDIUM (P2) - Document Misinterpretation Spiral                                                                                                                                    
                                                                                                                                                                                        
  Impact: Causes accusatory tone, wastes time on definitional mismatches                                                                                                                
  - Triggered safety compliance spiral in one instance                                                                                                                                  
  - System drilled into "verification" when terminology was misaligned                                                                                                                  
  - Root cause: No definition alignment step before deep drilling                                                                                                                       
  - Fix complexity: Medium - modify comparison logic in prompts + add clarification pattern                                                                                             
                                                                                                                                                                                        
  Why P2: Important for interview quality and user experience, but less frequent than P0/P1. Can be mitigated by P0+P1 fixes in the interim.                                            
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  🟢 LOW (P3) - Category Classification Bypass                                                                                                                                          
                                                                                                                                                                                        
  Impact: Follow-up questions escape counter by being classified as new openers                                                                                                         
  - LLM may classify subsequent questions as interview_note instead of followup                                                                                                         
  - Root cause: Counter relies on LLM category, not API-layer tracking                                                                                                                  
  - Fix complexity: Low - track at API layer regardless of LLM category                                                                                                                 
                                                                                                                                                                                        
  Why P3: This is a secondary reinforcement to P0. If P0 is fixed properly (counting at API layer), this becomes a non-issue.                                                           
                                                                                                                                                                                        
  ---                                                                                                                                                                                   
  Recommended Fix Order                                                                                                                                                                 
  ┌──────────┬──────────────────────┬────────────┬─────────────────────┐                                                                                                                
  │ Priority │        Issue         │   Effort   │     Dependency      │                                                                                                                
  ├──────────┼──────────────────────┼────────────┼─────────────────────┤                                                                                                                
  │ P0       │ Follow-up limiter    │ Medium     │ None - core fix     │                                                                                                                
  ├──────────┼──────────────────────┼────────────┼─────────────────────┤                                                                                                                
  │ P1       │ "Move on" command    │ Low-Medium │ None - independent  │                                                                                                                
  ├──────────┼──────────────────────┼────────────┼─────────────────────┤                                                                                                                
  │ P2       │ Definition alignment │ Medium     │ Benefits from P0/P1 │                                                                                                                
  ├──────────┼──────────────────────┼────────────┼─────────────────────┤                                                                                                                
  │ P3       │ Category bypass      │ Low        │ Solved by P0        │                                                                                                                
  └──────────┴──────────────────────┴────────────┴─────────────────────┘                                                                                                                
  ---                                                                                                                                                                                   
  Would you like me to create a detailed implementation plan for fixing these issues? If so, which ones should I prioritize?                                                            
  - Option A: Fix P0 + P1 (the two blockers)                                                                                                                                            
  - Option B: Fix all (P0 + P1 + P2 + P3)                                                                                                                                               
  - Option C: Fix P0 only first (smallest scope, highest impact)  
