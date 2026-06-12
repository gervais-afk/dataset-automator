---
title: Create Multi-Agent Team with CrewAI
domain: agentic_ai
type: procedure
---

# Procedure: Create Multi-Agent Team with CrewAI

**Objective**: 

## Steps
### Step 1: Instancier les agents
```python
from crewai import Agent
researcher = Agent(role='Researcher', goal='Find latest AI trends', backstory='Expert data gatherer')
writer = Agent(role='Writer', goal='Draft blog post', backstory='Tech writer')
```
**Tools**: N/A

### Step 2: Définir les tâches
```python
from crewai import Task
task1 = Task(description='Research agentic AI', expected_output='Bullet points', agent=researcher)
task2 = Task(description='Write post', expected_output='Markdown blog', agent=writer)
```
**Tools**: N/A

### Step 3: Assembler le Crew
```python
from crewai import Crew, Process
crew = Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)
```
**Tools**: N/A

**Validation/Pitfalls**: 
