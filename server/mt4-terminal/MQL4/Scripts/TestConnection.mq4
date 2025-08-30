//+------------------------------------------------------------------+
//|                                              TestConnection.mq4 |
//|                                         Test MT4 Functionality  |
//+------------------------------------------------------------------+
#property copyright "Test"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Script program start function                                   |
//+------------------------------------------------------------------+
void OnStart()
{
   // Write test information to file
   string filename = "test_connection.txt";
   int filehandle = FileOpen(filename, FILE_WRITE|FILE_TXT);
   
   if(filehandle != INVALID_HANDLE)
   {
      FileWriteString(filehandle, "MT4 Test Script Execution Report\n");
      FileWriteString(filehandle, "=================================\n\n");
      
      // Terminal information
      FileWriteString(filehandle, "Terminal Information:\n");
      FileWriteString(filehandle, "Terminal Company: " + TerminalCompany() + "\n");
      FileWriteString(filehandle, "Terminal Name: " + TerminalName() + "\n");
      FileWriteString(filehandle, "Terminal Path: " + TerminalPath() + "\n");
      FileWriteString(filehandle, "Data Path: " + TerminalInfoString(TERMINAL_DATA_PATH) + "\n");
      FileWriteString(filehandle, "Build: " + IntegerToString(TerminalInfoInteger(TERMINAL_BUILD)) + "\n\n");
      
      // Account information
      FileWriteString(filehandle, "Account Information:\n");
      FileWriteString(filehandle, "Account Number: " + IntegerToString(AccountNumber()) + "\n");
      FileWriteString(filehandle, "Account Name: " + AccountName() + "\n");
      FileWriteString(filehandle, "Account Server: " + AccountServer() + "\n");
      FileWriteString(filehandle, "Account Company: " + AccountCompany() + "\n");
      FileWriteString(filehandle, "Account Currency: " + AccountCurrency() + "\n");
      FileWriteString(filehandle, "Account Balance: " + DoubleToString(AccountBalance(), 2) + "\n");
      FileWriteString(filehandle, "Account Equity: " + DoubleToString(AccountEquity(), 2) + "\n");
      FileWriteString(filehandle, "Account Leverage: 1:" + IntegerToString(AccountLeverage()) + "\n");
      
      // Connection status
      FileWriteString(filehandle, "\nConnection Status:\n");
      if(IsConnected())
         FileWriteString(filehandle, "Status: CONNECTED\n");
      else
         FileWriteString(filehandle, "Status: DISCONNECTED\n");
      
      // Trade allowed status
      if(IsTradeAllowed())
         FileWriteString(filehandle, "Trading: ALLOWED\n");
      else
         FileWriteString(filehandle, "Trading: NOT ALLOWED\n");
      
      // Symbol information
      FileWriteString(filehandle, "\nCurrent Symbol: " + Symbol() + "\n");
      FileWriteString(filehandle, "Current Bid: " + DoubleToString(Bid, Digits) + "\n");
      FileWriteString(filehandle, "Current Ask: " + DoubleToString(Ask, Digits) + "\n");
      
      // Time information
      FileWriteString(filehandle, "\nTime Information:\n");
      FileWriteString(filehandle, "Server Time: " + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\n");
      FileWriteString(filehandle, "Local Time: " + TimeToString(TimeLocal(), TIME_DATE|TIME_SECONDS) + "\n");
      
      FileWriteString(filehandle, "\n=================================\n");
      FileWriteString(filehandle, "Test Completed Successfully!\n");
      
      FileClose(filehandle);
      Print("Test file created successfully: ", filename);
      
      // Also print to journal
      Print("=== MT4 Test Results ===");
      Print("Terminal: ", TerminalCompany(), " ", TerminalName());
      Print("Account: ", AccountNumber(), " (", AccountName(), ")");
      Print("Server: ", AccountServer());
      Print("Connection: ", IsConnected() ? "CONNECTED" : "DISCONNECTED");
      Print("Balance: ", AccountBalance());
      Print("Symbol: ", Symbol());
   }
   else
   {
      Print("Error: Could not create test file!");
   }
}