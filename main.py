import ts3
import sqlite3 as sql
import configparser

def isValidChannel(ts3conn, channelid):
    try:
        ts3conn.channelinfo(cid=channelid)[0]
        print("Valid!")
        return True
    except ts3.query.TS3QueryError:
        print("Invalid")
        return False

def sendchat(ts3conn, message, errormsg = False):
    if (styling == True):
        if (errormsg == True):
            ts3conn.sendtextmessage(targetmode=2, target=1, msg="[B][COLOR=#ff0000]" + message + "[/COLOR][/B]")
        else:
            ts3conn.sendtextmessage(targetmode=2, target=1, msg="[B]" + message + "[/B]")
    else:
        ts3conn.sendtextmessage(targetmode=2, target=1, msg=message)

def moduser(ts3conn, uid, user, remove):
    try:
        db.execute('SELECT CHANNELID FROM ChannelAdmins WHERE ADMIN = ?', (uid,))
    except Exception:
        print('Sqlite Exception: ' + Exception)
        sendchat(ts3conn, 'Internal Server Error', True)

    channel = db.fetchone();
    if (channel != None): #We have a match, the user is authorized!
        try:
            founduid = ts3conn.clientdbfind(pattern=user)[0]['cldbid']
            if (remove ==  True):
                print('Removing ' + user + ' (UID:' + founduid + ') from channel ID ' + str(channel[0]))
                ts3conn.setclientchannelgroup(cgid=guestgroup, cid=str(channel[0]), cldbid=founduid)
                sendchat(ts3conn, 'Removing ' + user + ' from ' + ts3conn.channelinfo(cid=channel[0])[0]['channel_name'] )
            else:
                print('Adding ' + user + ' (UID:' + founduid + ') to channel ID ' + str(channel[0]))
                ts3conn.setclientchannelgroup(cgid=allowedgroup, cid=str(channel[0]), cldbid=founduid)
                sendchat(ts3conn, 'Adding ' + user + ' to ' + ts3conn.channelinfo(cid=channel[0])[0]['channel_name'] )
        except ts3.query.TS3QueryError:
            print('User ' + user + ' not found')
            sendchat(ts3conn, 'Error: User not Found', True)
    else:
        print("ID " + uid + "is not authorized!")
        sendchat(ts3conn, 'Error: Permission Denied', True)

def modadmin(ts3con, uid, user, channelid, remove):
    if (channelid.isdigit()):  #If channel ID is not digit, returns same error as no user. Account for this here
        if(isValidChannel(ts3conn, channelid)):
            if (uid == adminuid):
                try:
                    founddbid = ts3conn.clientdbfind(pattern=user)[0]['cldbid'] #Get DB ID from name
                    cluid = ts3conn.clientdbinfo(cldbid=founddbid)[0]['client_unique_identifier'] #Get UID from DB id
                    if (remove == True):
                        db.execute('DELETE FROM ChannelAdmins WHERE CHANNELID = ? AND ADMIN = ?', (channelid, cluid))
                        sendchat(ts3conn, 'Removed ' + user + ' from admin of ' + ts3conn.channelinfo(cid=channelid)[0]['channel_name'])
                    else:
                        db.execute('INSERT INTO ChannelAdmins (CHANNELID, ADMIN) VALUES (?, ?)', (channelid, cluid))
                        sendchat(ts3conn, 'Added ' + user + ' as admin of ' + ts3conn.channelinfo(cid=channelid)[0]['channel_name'])
                except ts3.query.TS3QueryError:
                    print('User ' + user + ' not found while changing admin')
                    sendchat(ts3conn, 'Error: User not Found', True)
            else:
                print('Permission denied to add admin: ' + uid)
                sendchat(ts3conn, 'Error: Permission Denied', True)
        else:
            print('Invalid channel ID: ' + channelid)
            sendchat(ts3conn, 'Error: Invalid Channel ID', True)
    else:
        print('Malformed channel ID: ' + channelid)
        sendchat(ts3conn, 'Error: channel ID must be an integer', True)

def checkchat(ts3conn):
    ts3conn.servernotifyregister(event='textchannel')
    while True:
        ts3conn.send_keepalive()
        try:
        # This method blocks, but we must sent the keepalive message at
        # least once in 10 minutes. So we set the timeout parameter to
        # 9 minutes.
            event = ts3conn.wait_for_event(timeout=550)
        except ts3.query.TS3TimeoutError:
            pass

        else:
            if (event[0]['invokername'] != nickname ): #Prevent Feedback loops from bot responses!
                message = event[0]['msg']
                invokeruid = event[0]['invokeruid']
                if (message[0] == '!'): # If its actually a command
                    if (message[:4] == '!add') and (message[4] == ' '): #Lets add person to the whitelist
                        user = message[5:]
                        moduser(ts3conn, invokeruid, user, False)
                    elif (message[:4] == '!del') and (message[4] == ' '): #Lets remove person from the whitelist
                        user = message[5:]
                        moduser(ts3conn, invokeruid, user, True)
                    elif (message[:9] == '!adminadd') and (message[9] == ' '): #Lets add person to admin DB
                        userinput = message[10:].split(' ', 1)
                        if (len(userinput) == 2):
                            channelid = userinput[0]
                            user = userinput[1]
                            modadmin(ts3conn, invokeruid, user, channelid, False)
                        else:
                            print('Unrecognized parameters of adminadd: ' + message[10:])
                            sendchat(ts3conn, 'Error: !adminadd [channelid] [admin name]', True)
                    elif (message[:9] == '!admindel') and (message[9] == ' '): #Lets delete person from admin DB
                        userinput = message[10:].split(' ', 1)
                        if (len(userinput) == 2):
                            channelid = userinput[0]
                            user = userinput[1]
                            modadmin(ts3conn, invokeruid, user, channelid, True)
                        else:
                            print('Unrecognized parameters of admindel: ' + message[10:])
                            sendchat(ts3conn, 'Error: !admindel [channelid] [admin name]', True)
                    else:
                        print('Unrecognized Command: ' + message)
                        sendchat(ts3conn, 'Error: Unrecognized Command ' + message, True)
    return None


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('selfserve.cfg')

    hostname = config['connection'].get('hostname', '127.0.0.1')
    port = config['connection'].getint('port', '10011')
    loginname = config['connection'].get('username')
    loginpass = config['connection'].get('password')
    adminuid = config['connection'].get('adminuid')
    allowedgroup = config['groups'].get('allowed_group', '9')
    guestgroup = config['groups'].get('guest_group', '8')
    nickname = config['cosmetic'].get('nickname', 'SelfServe')
    styling = config['cosmetic'].getboolean('styling', True)

    if ((loginname == '') or (loginpass ==  '') or (adminuid == '')):
        print('Could not read selfserve.cfg. Please ensure it exists and is formatted correctly. Check the sample config for more info.')
        exit()

    #Start the DB connection, create the table
    dbcon = sql.connect('users.db')
    db = dbcon.cursor()
    db.execute('CREATE TABLE IF NOT EXISTS ChannelAdmins (ID INT PRIMARY KEY, CHANNELID INT NOT NULL, ADMIN TEXT NOT NULL)')

    #Lets Connect!
    with ts3.query.TS3Connection(hostname, port) as ts3conn:
        ts3conn.login(client_login_name=loginname, client_login_password=loginpass)
        ts3conn.use(sid=1)
        ts3conn.clientupdate(client_nickname=nickname)
        checkchat(ts3conn)
