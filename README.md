# count-1-million 
An example of a concurrent priority queue, using web sockets.
Syncs a counter across all connected clients, and queues the clients work in the order they connected
to the website. On a client disconnect while working, immediatly goes to the next user in the queue.

Known bug on Safari where the Safari browser seems to cache the websocket, and you need to restart
the browser to obtain the new connection on server restart.