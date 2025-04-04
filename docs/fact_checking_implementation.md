# Fact-Checking Implementation for DopCast Scripts

## Problem Statement

The current script generation process produces content with numerous factual inaccuracies. For example, in a recent script about the 2023 Monaco Grand Prix, over 25 factual errors were identified, including:

```
**Sam:** Alright everyone, welcome back to DopCast! Sam here, ready to dissect another Grand Prix. And what a race we have to unpack today – Monaco 2023! A classic Monaco race, really, with all the usual drama and a few unexpected twists.
```

While the introduction sounds engaging, subsequent sections contained significant errors such as:

- Incorrectly stating qualifying was held in wet conditions (it was dry)
- Claiming there was a red flag during the race (there wasn't one)
- Misrepresenting driver qualifying and finishing positions
- Incorrectly describing team strategies and pit stop decisions
- Fabricating incidents between drivers that didn't occur

These inaccuracies undermine the credibility of the content and could mislead listeners.

## Root Causes

1. **Poor Research Data Integration**: Research data isn't being properly incorporated into script generation
2. **Lack of Fact-Checking**: No verification of basic facts before finalizing scripts
3. **LLM Hallucinations**: The model creates events that never happened (like a red flag)
4. **Confusion Between Entities**: Mixing up driver positions, team strategies, etc.
5. **Over-Generalization**: Applying generic motorsport narratives without race-specific facts

## Proposed Solution: Fact-Checking Agent

We propose implementing a dedicated fact-checking agent as part of the script generation workflow:

```
Research → Content Planning → Script Draft → FACT CHECKING → Final Script
```

### Architecture Overview

The fact-checking agent will consist of five core components:

1. **Structured Race Data Repository**
2. **Fact Extraction Module**
3. **Verification Engine**
4. **Correction Suggestion Module**
5. **Confidence Scoring System**

## Authoritative Data Sources

The fact-checking agent will rely on these sources:

### Primary Sources (Official)
- FIA Official Documents (Race Classification, Qualifying Results, Stewards' Decisions)
- Formula 1 Official Website/API (Live Timing Data, Race Reports)
- Team Press Releases (Official Statements, Post-Race Reports)

### Secondary Sources (Reliable)
- F1TV Archive Footage (Race Broadcasts, Team Radio)
- Reputable Motorsport Publications (Autosport, Motorsport.com, The Race, RaceFans)
- Telemetry Data Providers (FastF1 Python library)

## Implementation Details

### 1. Structured Race Data Schema

Each race will have a comprehensive JSON schema:

```json
{
  "event": {
    "name": "Monaco Grand Prix",
    "year": 2023,
    "round": 7,
    "circuit": "Circuit de Monaco",
    "date": "2023-05-28"
  },
  "conditions": {
    "qualifying": ["dry", "sunny", "22°C"],
    "race": ["dry start", "rain from lap 50", "18-22°C"]
  },
  "qualifying_results": [
    {
      "position": 1,
      "driver": "Max Verstappen",
      "team": "Red Bull Racing",
      "time": "1:11.365",
      "grid_penalty": null
    },
    {
      "position": 2,
      "driver": "Fernando Alonso",
      "team": "Aston Martin",
      "time": "1:11.449",
      "grid_penalty": null
    }
    // Additional entries...
  ],
  "race_results": [
    {
      "position": 1,
      "driver": "Max Verstappen",
      "team": "Red Bull Racing",
      "grid": 1,
      "status": "Finished",
      "points": 25
    }
    // Additional entries...
  ],
  "key_events": [
    {
      "lap": 1,
      "type": "VSC",
      "description": "Virtual Safety Car deployed for incident at Turn 1",
      "duration": "2 minutes"
    },
    {
      "lap": 55,
      "type": "Strategy",
      "description": "Alonso pits for Medium tires during rain, then pits again next lap for Intermediates",
      "teams_involved": ["Aston Martin"]
    }
    // Additional events...
  ],
  "pit_stops": [
    {
      "driver": "Esteban Ocon",
      "lap": 33,
      "duration": "2.4 seconds",
      "tire_change": "Medium to Hard"
    }
    // Additional pit stops...
  ],
  "fastest_laps": [
    {
      "driver": "Lewis Hamilton",
      "lap": 70,
      "time": "1:15.650"
    }
    // Additional fastest laps...
  ]
}
```

### 2. Fact Extraction Module

This component will:

1. Parse the script to identify factual claims
2. Categorize claims by type (qualifying position, race result, strategy, weather, etc.)
3. Extract entities (drivers, teams, lap numbers, etc.)

```python
def extract_facts(script_text):
    facts = []
    
    # Use NLP to identify sentences with factual claims
    sentences = nlp_processor.split_into_sentences(script_text)
    
    for sentence in sentences:
        # Identify factual claims using pattern matching and NER
        if contains_factual_claim(sentence):
            claim_type = classify_claim_type(sentence)
            entities = extract_entities(sentence)
            
            facts.append({
                "text": sentence,
                "type": claim_type,
                "entities": entities,
                "confidence": calculate_confidence(sentence)
            })
    
    return facts
```

### 3. Verification Engine

This component will:

1. Match extracted facts against the structured race data
2. Calculate a confidence score for each verification
3. Flag inconsistencies and errors

```python
def verify_facts(extracted_facts, race_data):
    verification_results = []
    
    for fact in extracted_facts:
        if fact["type"] == "qualifying_position":
            driver = fact["entities"]["driver"]
            claimed_position = fact["entities"]["position"]
            
            # Find actual position in race data
            actual_position = find_qualifying_position(driver, race_data)
            
            is_correct = (claimed_position == actual_position)
            
            verification_results.append({
                "fact": fact,
                "is_correct": is_correct,
                "correct_value": actual_position,
                "confidence": 0.95 if is_correct else 0.90,
                "source": "FIA Official Qualifying Results"
            })
    
    return verification_results
```

### 4. Correction Suggestion Module

This component will:

1. Generate corrections for identified errors
2. Provide context and explanation for the corrections
3. Suggest alternative phrasings that maintain the narrative flow

```python
def generate_corrections(verification_results):
    corrections = []
    
    for result in verification_results:
        if not result["is_correct"]:
            fact = result["fact"]
            
            correction = {
                "original_text": fact["text"],
                "corrected_text": generate_corrected_text(fact, result["correct_value"]),
                "explanation": generate_explanation(fact, result),
                "source_reference": result["source"],
                "confidence": result["confidence"]
            }
            
            corrections.append(correction)
    
    return corrections
```

## Integration with Existing Workflow

The fact-checking agent will be integrated as follows:

### 1. Pre-Script Generation
- Provide verified race data to the script generation agent
- Include factual constraints in the system prompt

```python
system_prompt = f"""
You are generating dialogue about the {race_facts['race']['name']} {race_facts['race']['year']}.

IMPORTANT FACTUAL CONSTRAINTS:
- Qualifying results: {json.dumps(race_facts['qualifying_results'][:5])}
- Race results: {json.dumps(race_facts['race_results'][:5])}
- Weather conditions: {', '.join(race_facts['race']['weather_conditions'])}
- Safety cars: {json.dumps(race_facts['race']['safety_cars'])}
- Red flags: {json.dumps(race_facts['race']['red_flags'])}
- Key events: {json.dumps(race_facts['key_events'])}

You MUST NOT contradict these facts in your dialogue.
"""
```

### 2. Post-Script Generation
- Verify the generated script against the race data
- Apply corrections to factual errors

### 3. Interactive Correction
- Allow for human review of suggested corrections
- Provide confidence scores for each correction

## Example Workflow Node

```python
def fact_check_script(state: ScriptState) -> Dict[str, Any]:
    """
    Verify factual accuracy of the script against official race data.
    
    Args:
        state: Current state with draft script
        
    Returns:
        Updated state with verified script
    """
    logger.info("Fact-checking script")
    
    try:
        script = state.get("script", {})
        race_data = get_race_data(script.get("sport"), script.get("event_id"))
        
        # Extract all dialogue lines
        all_dialogue = []
        for section in script.get("sections", []):
            all_dialogue.extend(section.get("dialogue", []))
        
        # Extract facts from dialogue
        extracted_facts = extract_facts([line.get("text", "") for line in all_dialogue])
        
        # Verify facts against race data
        verification_results = verify_facts(extracted_facts, race_data)
        
        # Generate corrections
        corrections = generate_corrections(verification_results)
        
        # Apply corrections to script
        corrected_script = apply_corrections(script, corrections, all_dialogue)
        
        # Add verification metadata
        corrected_script["fact_check"] = {
            "verified_at": datetime.now().isoformat(),
            "facts_checked": len(extracted_facts),
            "corrections_made": len(corrections),
            "confidence": calculate_overall_confidence(verification_results)
        }
        
        logger.info(f"Fact-checking completed: {len(corrections)} corrections made")
        
        return {"script": corrected_script, "fact_check_results": verification_results}
    
    except Exception as e:
        logger.error(f"Error fact-checking script: {e}", exc_info=True)
        return {"error_info": f"Fact-checking failed: {str(e)}"}
```

## Automated Data Collection Pipeline

To maintain an up-to-date database of race facts:

1. **Race Weekend Crawler**: Automatically collect data during race weekends
2. **FIA Document Parser**: Extract official results from PDF documents
3. **Media Monitoring**: Collect team statements and press releases
4. **Data Validation**: Cross-reference multiple sources to ensure accuracy

## Handling Ambiguity and Uncertainty

For cases where facts are ambiguous or uncertain:

1. **Confidence Scoring**: Assign confidence levels to each verification
2. **Human Review Flagging**: Flag low-confidence verifications for human review
3. **Source Prioritization**: Prioritize official sources over secondary sources
4. **Temporal Context**: Consider when statements were made (pre-race vs. post-race)

## Implementation Timeline

1. **Phase 1** (2 weeks): Build structured race data repository for past races
   - Create JSON schema
   - Populate with data for recent races
   - Implement data validation

2. **Phase 2** (3 weeks): Implement fact extraction and verification engine
   - Develop NLP components for fact extraction
   - Build verification logic
   - Test against known errors

3. **Phase 3** (2 weeks): Develop correction suggestion module
   - Implement correction generation
   - Create explanation templates
   - Build confidence scoring system

4. **Phase 4** (1 week): Integrate with existing workflow
   - Add fact-checking node to workflow
   - Update script generation prompts
   - Implement pre/post-generation hooks

5. **Phase 5** (Ongoing): Implement automated data collection pipeline
   - Develop crawlers for official sources
   - Build parsers for structured data extraction
   - Set up continuous data validation

## Benefits

1. **Improved Accuracy**: Eliminate factual errors in scripts
2. **Increased Credibility**: Maintain audience trust through factual accuracy
3. **Efficiency**: Automate the fact-checking process
4. **Learning**: Improve the script generation model over time
5. **Transparency**: Provide sources for factual claims

## Example: Correcting Monaco 2023 Errors

Here's how the fact-checking agent would correct some of the errors from the Monaco 2023 script:

### Error 1: Qualifying Conditions
**Original**: "He [Verstappen] absolutely nailed that tricky qualifying in the wet, didn't he?"  
**Correction**: "He [Verstappen] absolutely nailed that tricky qualifying session, didn't he?"  
**Explanation**: Qualifying for the 2023 Monaco GP was held in dry conditions. The rain arrived during the race itself.

### Error 2: Red Flag Claim
**Original**: "Then, of course, the red flag later on after…Sainz clipped Ocon, I think?"  
**Correction**: "Then, of course, the challenging conditions later on when the rain started falling around lap 50."  
**Explanation**: There was no red flag during the 2023 Monaco Grand Prix. The race finished under green flag conditions.

### Error 3: Ferrari Qualifying Result
**Original**: "I think the biggest one has to be Ferrari. I mean, they locked out the front row, Leclerc on pole, Sainz right behind."  
**Correction**: "I think Ferrari had a mixed qualifying. Leclerc qualified P3 but started P6 due to a penalty, while Sainz started from P4."  
**Explanation**: Ferrari did not lock out the front row. Max Verstappen took pole position with Fernando Alonso in P2.

## Conclusion

Implementing this fact-checking agent will significantly improve the accuracy of DopCast scripts while maintaining the engaging, conversational style that makes the content compelling. By grounding the scripts in verified facts, we can ensure that listeners receive accurate information while enjoying the entertainment value of the podcast format.

The modular design allows for incremental implementation, starting with the most critical components (structured data and verification) and expanding to more sophisticated features over time.
