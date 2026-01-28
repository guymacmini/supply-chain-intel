# Task Reference - Quick Implementation Guide

## 📋 All Tasks at a Glance

### Feature 1: Enhanced Research Analysis (3 tasks)
```
[1.1] Add direct/indirect impact analysis to Explore Agent
[1.2] Add bullish/bearish investment recommendations
[1.3] Update markdown template with new sections
```
**Files**: `explore_agent.py`, `markdown_generator.py`
**Dependencies**: None
**Estimated effort**: 4-6 hours

### Feature 2: Optional API Integrations (3 tasks)
```
[2.1] Add FINNHUB_API_KEY and TAVILY_API_KEY to config
[2.2] Integrate Finnhub for market data (52W high/low, P/E, etc)
[2.3] Integrate Tavily for enhanced web search
```
**Files**: `.env.example`, `config_loader.py`, `explore_agent.py`, new `finnhub_client.py`, new `tavily_client.py`
**Dependencies**: `finnhub-python>=1.4.0`, `tavily-python>=0.3.0`
**Estimated effort**: 5-7 hours

### Feature 3: Interactive Follow-ups (4 tasks)
```
[3.1] Add "Ask Follow-up" button to document viewer UI
[3.2] Create /api/research/followup endpoint
[3.3] Extend Explore Agent with followup method
[3.4] Update GUI to show follow-up chain/history
```
**Files**: `document.html`, `history.html`, `app.py`, `explore_agent.py`
**Dependencies**: None
**Estimated effort**: 6-8 hours

---

## 🎯 Recommended Implementation Order

### Day 1: Foundation
**Morning**: Task 1.1, 1.2 (Enhanced analysis)
**Afternoon**: Task 1.3 (Template updates)
**Evening**: Test with multiple queries

### Day 2: Market Data
**Morning**: Task 2.1 (Config setup)
**Afternoon**: Task 2.2 (Finnhub integration)
**Evening**: Test with/without API keys

### Day 3: Interactive Features
**Morning**: Task 3.1, 3.2 (UI + API endpoint)
**Afternoon**: Task 3.3 (Follow-up logic)
**Evening**: Task 3.4 (History display)

### Day 4: Polish & Optional
**Morning**: Task 2.3 (Tavily - optional)
**Afternoon**: End-to-end testing
**Evening**: Documentation updates

---

## 🔧 Quick Start Checklist

### Before Starting Any Task
- [ ] Read the task description in fix_plan.md
- [ ] Read relevant section in NEW_FEATURES_SUMMARY.md
- [ ] Identify files to modify (listed in each task)
- [ ] Check if dependencies need to be added

### For Each Task
- [ ] Create branch: `git checkout -b feature/task-X-Y`
- [ ] Implement the feature
- [ ] Test manually (run the command/view in GUI)
- [ ] Test edge cases (missing API keys, etc.)
- [ ] Update fix_plan.md checkbox: `- [x] Task X.Y`
- [ ] Commit with descriptive message
- [ ] Move to next task

### After All Tasks
- [ ] Run full test suite: `make test`
- [ ] Test GUI end-to-end
- [ ] Update README if needed
- [ ] Update .env.example with new keys

---

## 📝 Testing Checklist

### Feature 1 Testing
- [ ] Research includes "Market Impact Analysis" section
- [ ] Both "Bullish Scenario" and "Bearish Scenario" present
- [ ] Investment recommendations have specific tickers
- [ ] Entry strategies and risk factors included
- [ ] Works with CLI: `./run.sh explore "AI chips"`
- [ ] Works with GUI: Explore page

### Feature 2 Testing
- [ ] Works WITHOUT Finnhub key (gracefully skips market data)
- [ ] Works WITH Finnhub key (includes market valuation table)
- [ ] Handles invalid API key gracefully
- [ ] Handles API rate limits gracefully
- [ ] Works WITHOUT Tavily key (uses Anthropic search)
- [ ] Works WITH Tavily key (uses Tavily search)

### Feature 3 Testing
- [ ] Follow-up button appears on research documents
- [ ] Clicking button shows form with text input
- [ ] Submitting question generates new markdown file
- [ ] Follow-up file references original research
- [ ] Follow-up appears in history with visual indicator
- [ ] Can chain multiple follow-ups (parent → child → grandchild)
- [ ] Follow-ups work from CLI: `./run.sh research followup <file> <question>`

---

## 🐛 Common Issues & Solutions

### Issue: Finnhub API rate limit exceeded
**Solution**: Add retry logic with exponential backoff, or cache results for 15min

### Issue: Follow-up loses context from original
**Solution**: Ensure original research content is included in Claude prompt

### Issue: Markdown formatting breaks with new sections
**Solution**: Use consistent heading levels (##) and verify with markdown preview

### Issue: GUI shows 500 error on follow-up
**Solution**: Check Flask logs, likely missing error handling in API endpoint

---

## 📚 Key Files Reference

```
src/
├── agents/
│   ├── explore_agent.py      # Tasks: 1.1, 1.2, 2.2, 2.3, 3.3
│   └── ...
├── utils/
│   ├── config_loader.py       # Task: 2.1
│   ├── markdown_generator.py  # Task: 1.3
│   ├── finnhub_client.py      # Task: 2.2 (NEW FILE)
│   └── tavily_client.py       # Task: 2.3 (NEW FILE)
├── web/
│   ├── app.py                 # Task: 3.2
│   └── templates/
│       ├── document.html      # Tasks: 3.1, 3.4
│       └── history.html       # Task: 3.4
├── .env.example               # Task: 2.1
├── requirements.txt           # Tasks: 2.2, 2.3 (add dependencies)
└── pyproject.toml             # Tasks: 2.2, 2.3 (add dependencies)
```

---

## 💡 Pro Tips

1. **Start with Task 1.1-1.3**: They provide the most value and require no new dependencies
2. **Test incrementally**: Don't wait until all tasks are done to test
3. **Make optional truly optional**: System should work great even without Finnhub/Tavily
4. **Use git branches**: Easy to isolate features and rollback if needed
5. **Update docs as you go**: Don't leave documentation for the end
6. **Test both CLI and GUI**: Features should work in both interfaces where applicable

---

## 📊 Progress Tracking

Track your progress by updating checkboxes in `.ralph/fix_plan.md`:

```bash
# Mark task complete
vim .ralph/fix_plan.md
# Change: - [ ] **Task 1.1**
# To:     - [x] **Task 1.1**

# View progress
grep "Task [123]\." .ralph/fix_plan.md | grep -c "\[x\]"  # Completed
grep "Task [123]\." .ralph/fix_plan.md | grep -c "\[ \]"  # Remaining
```

Current status: **0/10 tasks complete**

---

## 🚀 Ready to Start?

1. Read this file ✓
2. Read NEW_FEATURES_SUMMARY.md for detailed examples
3. Read fix_plan.md for task specifications
4. Pick Task 1.1 and start coding!

Good luck! 🎯
