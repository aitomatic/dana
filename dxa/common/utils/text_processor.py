class TextProcessor:
    def __init__(self):
        pass
    
    
    def parse_by_key(self, response, key):
        lines = response.split("\n")
        value = next((line.split(": ", 1)[1] for line in lines if line.startswith(f"{key}:")), "Unknown")
        return value
    
    def parse_code(self, response):
        start_tag = "<CODE>"
        end_tag = "</CODE>"
        
        start_index = response.find(start_tag)
        end_index = response.find(end_tag, start_index)
        
        if start_index == -1 or end_index == -1:
            return None
        
        # Extract the code between the <CODE> and </CODE> tags
        code = response[start_index + len(start_tag):end_index].strip()
        return code