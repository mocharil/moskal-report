import json
import os
import pandas as pd
import re

# Import utilitas dari paket utils (sesuaikan dengan environment Anda)
from chart_generator.functions import call_gemini

def generate_recommendations(TOPIC,START_DATE, END_DATE,SAVE_PATH):
   
    # Inisialisasi dictionary untuk menyimpan semua data
    data = {}
    
    # 1. Load sentiment_breakdown.json
    try:
        with open(os.path.join(SAVE_PATH, 'sentiment_breakdown.json'), 'r') as f:
            data['sentiment_counts'] = json.load(f)
        print("Loaded sentiment breakdown data")
    except Exception as e:
        print(f"Error loading sentiment breakdown: {e}")
        data['sentiment_counts'] = {}
    
    # 2. Load sentiment_by_categories.json
    try:
        with open(os.path.join(SAVE_PATH, 'sentiment_by_categories.json'), 'r') as f:
            data['pivot_sentiment'] = json.load(f)
        print("Loaded sentiment by categories data")
    except Exception as e:
        print(f"Error loading sentiment by categories: {e}")
        data['pivot_sentiment'] = []
    
    # 3. Load presence_score_analysis.json
    try:
        with open(os.path.join(SAVE_PATH, 'presence_score_analysis.json'), 'r') as f:
            data['presence_score_analysis'] = json.load(f)
        print("Loaded presence score analysis")
    except Exception as e:
        print(f"Error loading presence score analysis: {e}")
        data['presence_score_analysis'] = {}
    
    # 4. Load sentiment_analysis.json
    try:
        with open(os.path.join(SAVE_PATH, 'sentiment_analysis.json'), 'r') as f:
            data['sentiment_analysis'] = json.load(f)
        print("Loaded sentiment analysis")
    except Exception as e:
        print(f"Error loading sentiment analysis: {e}")
        data['sentiment_analysis'] = {}
    
    # 5. Load popular_mentions.csv
    try:
        data['popular_mentions'] = pd.read_csv(os.path.join(SAVE_PATH, 'popular_mentions.csv')).to_dict(orient='records')[:10]  # Limit to top 10
        print("Loaded popular mentions data")
    except Exception as e:
        print(f"Error loading popular mentions: {e}")
        data['popular_mentions'] = []
    
    # 6. Load KOL data
    try:
        kol_data = []
        with open(os.path.join(SAVE_PATH, 'kol.json'), 'r') as f:
            for line in f:
                kol_data.append(json.loads(line.strip()))
        data['kol_data'] = kol_data[:10]  # Limit to top 10
        print("Loaded KOL data")
    except Exception as e:
        print(f"Error loading KOL data: {e}")
        data['kol_data'] = []
    
    # 7. Load topic_overview.json
    try:
        topic_data = []
        with open(os.path.join(SAVE_PATH, 'topic_overview.json'), 'r') as f:
            for line in f:
                topic_data.append(json.loads(line.strip()))
        data['top_entities'] = topic_data[:15]  # Limit to top 15
        print("Loaded topic overview data")
    except Exception as e:
        print(f"Error loading topic overview: {e}")
        data['top_entities'] = []
    
    # Extract platform data from sentiment_by_categories.json for list of top platforms
    top_platforms = []
    if data['pivot_sentiment']:
        # Sort by total_mentions and get top 5 platforms
        sorted_platforms = sorted(data['pivot_sentiment'], key=lambda x: x.get('total_mentions', 0), reverse=True)
        top_platforms = [p.get('channel', '') for p in sorted_platforms[:5] if p.get('channel')]
    
    # Build the prompt
    prompt = f"""
    You are a senior digital communications and media strategy expert. Analyze the following comprehensive data about [{TOPIC}] for the period [{START_DATE}] to [{END_DATE}] and provide strategic recommendations.

    ## SENTIMENT DATA
    
    Overall sentiment distribution:
    {data['sentiment_counts']}
    
    Sentiment by platform/channel:
    {data['pivot_sentiment'][:5] if data['pivot_sentiment'] else "No data available"}
    """
    
    # Add presence score analysis if available
    if data['presence_score_analysis']:
        prompt += f"""
    ## PRESENCE SCORE ANALYSIS
    
    Overall presence score trends:
    {data['presence_score_analysis']}
    """
    
    # Add sentiment analysis if available
    if data['sentiment_analysis']:
        prompt += f"""
    ## DETAILED SENTIMENT ANALYSIS
    
    In-depth sentiment analysis:
    {data['sentiment_analysis']}
    """
    
    # Add popular mentions if available
    if data['popular_mentions']:
        prompt += f"""
    ## POPULAR MENTIONS
    
    Sample of popular posts (top shown):
    {data['popular_mentions'][:3]}
    """
    
    # Add top entities if available
    if data['top_entities']:
        prompt += f"""
    ## TOP ENTITIES/TOPICS
    
    Most discussed entities or subtopics:
    {data['top_entities'][:10]}
    """
    
    # Add KOL data if available
    if data['kol_data']:
        prompt += f"""
    ## KEY OPINION LEADERS
    
    Top influencers discussing this topic:
    {data['kol_data'][:5]}
    """
    
    # Add list of top platforms
    prompt += f"""
    ## TOP PLATFORMS
    
    The most active platforms for this topic are:
    {top_platforms if top_platforms else "Data not available"}
    """
    
    # Instruksi dan format output
    prompt += f"""
    ## TASK
    
    Based on all the data above, provide strategic communication recommendations for managing and improving the discourse around [{TOPIC}].

    Format your response as a JSON array with EXACTLY 4 recommendation categories (no more, no less), each with:
    - "title": A clear, specific category description focusing on communication strategy (limit to 10 words)
    - "actions": An array of EXACTLY 3 specific, actionable steps (each 1-2 sentences long)

    The recommendations should be highly specific to {TOPIC} and directly address the sentiment, trends, and key concerns found in the data. DO NOT provide generic advice.

    Each recommendation should be concrete, implementable, and directly tied to the data insights provided.

    THE OUTPUT MUST BE VALID JSON. Use this exact format:
    [
      {{
        "title": "Strategy Category Title",
        "actions": [
          "Specific actionable step one with clear direction.",
          "Specific actionable step two with clear direction.",
          "Specific actionable step three with clear direction."
        ]
      }},
      ...
    ]

    IMPORTANT: Ensure your output is ONLY the properly formatted JSON with no additional text, markdown, or explanatory content. The JSON array must contain EXACTLY 4 recommendation objects. Each recommendation must have EXACTLY 3 actions.
    """
    
    print("Prompt generated, calling LLM...")
    
    try:
        # Call LLM to generate recommendations
        recommendations_text = call_gemini(prompt)
        
        # Try to parse JSON directly
        try:
     
            recommendations  = json.loads(re.findall(r'\{.*\}',recommendations_text, flags = re.I|re.S)[0])
        except json.JSONDecodeError as e:
            print(f"Direct JSON parsing failed with error: {e}")
            # Use regex as fallback if direct parsing fails
            print("Direct JSON parsing failed, trying regex extraction...")
            json_pattern = re.compile(r'\[\s*\{.*\}\s*\]', re.DOTALL)
            json_match = json_pattern.search(recommendations_text)
            
            if json_match:
                json_str = json_match.group(0)
                recommendations = json.loads(json_str)
            else:
                # Last-resort fallback parsing for valid portions
                print("Regex extraction failed, trying fallback parsing...")
                title_pattern = re.compile(r'"title":\s*"([^"]+)"')
                actions_pattern = re.compile(r'"actions":\s*\[(.*?)\]', re.DOTALL)
                action_item_pattern = re.compile(r'"([^"]+)"')
                
                recommendations = []
                
                # Find all title matches
                title_matches = title_pattern.finditer(recommendations_text)
                for title_match in title_matches:
                    title = title_match.group(1)
                    # Find corresponding actions
                    actions_match = actions_pattern.search(recommendations_text, title_match.end())
                    if actions_match:
                        actions_text = actions_match.group(1)
                        actions = [m.group(1) for m in action_item_pattern.finditer(actions_text)]
                        if actions:
                            recommendations.append({"title": title, "actions": actions})
                
        # Save the recommendations to file
        with open(os.path.join(SAVE_PATH, 'recommendations.json'), 'w') as f:
            json.dump(recommendations, f, indent=2)
            
        print(f"Recommendations generated and saved to {os.path.join(SAVE_PATH, 'recommendations.json')}")
        return recommendations
        
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        # Return fallback recommendations
        fallback_recommendations = [
            {
                "title": "Error Processing Data",
                "actions": [
                    "Review input data files for completeness and formatting issues.",
                    "Check LLM connection and retry with simplified prompt.",
                    "Consider manual analysis if automation continues to fail."
                ]
            }
        ]
        
        with open(os.path.join(SAVE_PATH, 'recommendations_error.json'), 'w') as f:
            json.dump(fallback_recommendations, f, indent=2)
            
        return fallback_recommendations

