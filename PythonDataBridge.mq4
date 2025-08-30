//+------------------------------------------------------------------+
//|                                            PythonDataBridge.mq4 |
//|                        Python Integration Bridge for MT4        |
//+------------------------------------------------------------------+
#property copyright "MQL-Python Converter"
#property version   "1.00"
#property strict

// Input parameters
input string PythonServerIP = "127.0.0.1";
input int    PythonServerPort = 9999;
input int    SendIntervalMs = 1000;

// Global variables
int socket = INVALID_HANDLE;
datetime lastSendTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("Python Data Bridge EA initialized");
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    if(socket != INVALID_HANDLE)
    {
        SocketClose(socket);
    }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check send interval
    if(TimeLocal() - lastSendTime < SendIntervalMs/1000)
        return;
    
    // Prepare data
    string data = StringFormat("{\"symbol\":\"%s\",\"time\":\"%s\",\"bid\":%f,\"ask\":%f,\"spread\":%d}",
                              Symbol(),
                              TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
                              Bid,
                              Ask,
                              (int)MarketInfo(Symbol(), MODE_SPREAD));
    
    // Send to Python
    if(SendDataToPython(data))
    {
        lastSendTime = TimeLocal();
    }
}

//+------------------------------------------------------------------+
//| Send data to Python server                                      |
//+------------------------------------------------------------------+
bool SendDataToPython(string data)
{
    // Create socket if needed
    if(socket == INVALID_HANDLE)
    {
        socket = SocketCreate();
        if(socket == INVALID_HANDLE)
        {
            Print("Failed to create socket");
            return false;
        }
    }
    
    // Connect to Python server
    if(!SocketConnect(socket, PythonServerIP, PythonServerPort, 1000))
    {
        Print("Failed to connect to Python server");
        SocketClose(socket);
        socket = INVALID_HANDLE;
        return false;
    }
    
    // Send data
    char req[];
    StringToCharArray(data, req);
    int sent = SocketSend(socket, req, ArraySize(req));
    
    if(sent <= 0)
    {
        Print("Failed to send data");
        SocketClose(socket);
        socket = INVALID_HANDLE;
        return false;
    }
    
    // Receive acknowledgment
    char resp[];
    int received = SocketRead(socket, resp, 2, 1000);
    
    // Close connection
    SocketClose(socket);
    socket = INVALID_HANDLE;
    
    return true;
}

//| Alternative: Save data to file for Python to read               |
//+------------------------------------------------------------------+
void SaveDataToFile()
{
    string filename = "python_bridge_data.csv";
    int handle = FileOpen(filename, FILE_WRITE|FILE_CSV);
    
    if(handle != INVALID_HANDLE)
    {
        FileWrite(handle, Symbol(), TimeCurrent(), Bid, Ask, 
                 MarketInfo(Symbol(), MODE_SPREAD),
                 AccountBalance(), AccountEquity());
        FileClose(handle);
    }
}
//+------------------------------------------------------------------+
