import sys
import traceback

def get_detailed_error_message(error_message: str, error_detail: sys) -> str:
    """
    Extracts the exact filename and line number from the system traceback buffer
    so you know exactly where your code crashed without having to hunt for it.
    """
    # exc_info() returns a tuple of (type, value, traceback)
    _, _, exc_tb = error_detail.exc_info()
    
    if exc_tb is not None:
        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        
        detailed_message = (
            f"Error occurred in python script name [{file_name}] "
            f"at line number [{line_number}] "
            f"Error message: [{str(error_message)}]"
        )
    else:
        detailed_message = str(error_message)
        
    return detailed_message


class EnergyDocsException(Exception):
    """
    A custom exception class for the RAG pipeline that automatically captures 
    the system traceback and pinpoints the file and line of the error.
    
    Usage:
        try:
            a = 1 / 0
        except Exception as e:
            raise EnergyDocsException(e, sys)
    """
    def __init__(self, error_message: Exception | str, error_detail: sys):
        # Initialize the base Exception class
        super().__init__(error_message)
        
        # Override the error message with our highly detailed traceback string
        self.error_message = get_detailed_error_message(
            error_message=str(error_message), 
            error_detail=error_detail
        )

    def __str__(self):
        """
        When the exception is printed or logged, it returns the detailed error string.
        """
        return self.error_message
