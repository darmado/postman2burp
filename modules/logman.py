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
    
    print(f"Debug: Saving results to directory: {output_dir}")
    
    # Create output directory if it doesn't exist
    if not ensure_log_directory(output_dir):
        print(f"Debug: Failed to create directory: {output_dir}")
        return None
    
    # Generate filename based on collection name and timestamp
    collection_name = os.path.splitext(os.path.basename(collection_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{collection_name}_{timestamp}.json"
    output_path = os.path.join(output_dir, filename)
    
    print(f"Debug: Output path: {output_path}")
    
    # Extract proxy information
    proxy_host, proxy_port = proxy_info if proxy_info else (None, None)
    
    # Add metadata to results
    results_copy = results.copy()
    results_copy["metadata"] = {
        "collection": os.path.basename(collection_path),
        "insertion_point": os.path.basename(target_insertion_point) if target_insertion_point else None,
        "proxy": f"{proxy_host}:{proxy_port}" if proxy_host and proxy_port else "None",
        "timestamp": datetime.now().isoformat(),
        "total_requests": len(results_copy["requests"]),
        "successful_requests": sum(1 for r in results_copy["requests"] if r.get("success", False)),
        "failed_requests": sum(1 for r in results_copy["requests"] if not r.get("success", False))
    }
    
    # Save results
    try:
        with open(output_path, 'w') as f:
            json.dump(results_copy, f, indent=2)
        print(f"Debug: Successfully saved results to {output_path}")
        logger.info(f"Results saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Debug: Error saving results: {e}")
        logger.error(f"Could not save results: {e}")
        return None 