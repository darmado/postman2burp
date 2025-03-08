import os
import logging
import json
from datetime import datetime

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging(log_level=logging.INFO, log_file=None, verbose=False):
    """
    Configure the logging system.
    
    Args:
        log_level (int): The logging level (e.g., logging.INFO, logging.DEBUG)
        log_file (str): Path to the log file
        verbose (bool): Whether to enable verbose logging
        
    Returns:
        logging.Logger: Configured logger
    """
    # Set up basic configuration
    logging_config = {
        'level': logging.DEBUG if verbose else log_level,
        'format': DEFAULT_LOG_FORMAT
    }
    
    # Add file handler if log_file is specified
    if log_file:
        # Ensure the directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        logging_config['filename'] = log_file
    
    # Apply configuration
    logging.basicConfig(**logging_config)
    
    # Get the logger
    logger = logging.getLogger('repl')
    
    # Set console handler level based on verbose flag
    if verbose:
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)
    
    return logger

def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

def ensure_log_directory(log_dir):
    """
    Ensure that the log directory exists.
    
    Args:
        log_dir (str): Path to the log directory
        
    Returns:
        bool: True if the directory exists or was created, False otherwise
    """
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            logging.debug(f"Created log directory: {log_dir}")
        return True
    except Exception as e:
        logging.error(f"Could not create log directory: {e}")
        return False

def save_results_to_file(results, collection_path, target_insertion_point, proxy_info, output_dir, logger=None):
    """
    Save the results to a file.
    
    Args:
        results (dict): The results to save
        collection_path (str): Path to the collection file
        target_insertion_point (str): Path to the insertion point file
        proxy_info (tuple): Tuple containing proxy host and port
        output_dir (str): Directory to save the results
        logger (logging.Logger): Logger instance
        
    Returns:
        str: Path to the saved file, or None if saving failed
    """
    if logger is None:
        logger = logging.getLogger('repl')
    
    # Create output directory if it doesn't exist
    if not ensure_log_directory(output_dir):
        logger.error(f"Failed to create directory: {output_dir}")
        return None
    
    # Generate collection-specific log directory
    collection_name = os.path.splitext(os.path.basename(collection_path))[0]
    collection_log_dir = os.path.join(output_dir, collection_name)
    
    # Create collection-specific log directory if it doesn't exist
    if not ensure_log_directory(collection_log_dir):
        logger.error(f"Failed to create collection log directory: {collection_log_dir}")
        return None
    
    # Generate timestamp for the log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a structured directory based on the collection hierarchy
    try:
        # Group requests by folder
        folder_requests = {}
        for request in results.get('requests', []):
            folder = request.get('folder', '')
            if folder not in folder_requests:
                folder_requests[folder] = []
            folder_requests[folder].append(request)
        
        # Create folder structure and save requests
        for folder, requests in folder_requests.items():
            folder_path = collection_log_dir
            
            # Create nested folders if needed
            if folder:
                folder_parts = folder.split('/')
                for part in folder_parts:
                    folder_path = os.path.join(folder_path, part)
                    if not ensure_log_directory(folder_path):
                        logger.error(f"Failed to create folder: {folder_path}")
                        continue
            
            # Save each request in its own file
            for request in requests:
                request_name = request.get('name', 'unknown_request')
                # Sanitize filename
                request_name = request_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                request_filename = f"{request_name}_{timestamp}.json"
                request_path = os.path.join(folder_path, request_filename)
                
                # Add request ID if not present
                if 'id' not in request:
                    request['id'] = f"req_{timestamp}_{hash(request_name) % 10000:04d}"
                
                # Save individual request
                try:
                    with open(request_path, 'w') as f:
                        json.dump(request, f, indent=2)
                    logger.info(f"Saved request to {request_path}")
                except Exception as e:
                    logger.error(f"Failed to save request to {request_path}: {e}")
    except Exception as e:
        logger.error(f"Failed to create structured log: {e}")
    
    # Also save the complete results file for backward compatibility
    filename = f"{collection_name}_{timestamp}.json"
    output_path = os.path.join(output_dir, filename)
    
    # Add metadata
    metadata = {
        "collection": os.path.basename(collection_path),
        "timestamp": timestamp,
        "proxy": f"{proxy_info[0]}:{proxy_info[1]}" if proxy_info else None,
        "insertion_point": os.path.basename(target_insertion_point) if target_insertion_point else None
    }
    
    results["metadata"] = metadata
    
    # Save to file
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return None 