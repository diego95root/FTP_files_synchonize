from ftplib import FTP
import os
import hashlib
from datetime import datetime


def md5(file):
    hash_md5 = hashlib.md5()
    with open(file, "rb") as fi:
        for each in iter(lambda: fi.read(4096), b""):
            hash_md5.update(each)
    return hash_md5.hexdigest()

class server():
    def __init__(self, host, username, password):

        self.host = host
        self.username = username
        self.time_init = datetime.now()

        self.ftp = FTP(host)
        #password = raw_input("Enter password of ftp account with username {}: ".format(username)) #add and remove fourth argument
        self.ftp.login(username, password)
        self.files_to_transfer = []

    def __str__(self):
        time_now = datetime.now()
        return '\n* Connected to host {} with username {}\n* Time elapsed since login: {}\n'.format(self.host, self.username, str(time_now-self.time_init))

    def list_directory(self): #print all files in cwd formatted command-line-like
        data = []
        self.ftp.dir(data.append)
        for line in data:
            print "-", line

    def compare_files(self, mypath, path):

        self.ftp.cwd(path)
        os.chdir(mypath)

        data = []
        self.ftp.dir(data.append)
        data = data[2:]
        print path

        for file_ in os.listdir(os.getcwd()):
            pass

    def get_ftp_md5(self, remote_path):
        m = hashlib.md5()
        self.ftp.retrbinary('RETR %s' % remote_path, m.update)
        return m.hexdigest()

    def walk(self, dir, path2):
        for i in os.listdir(dir):
            if os.path.isdir(os.path.join(dir, i)):
                self.ftp.mkd(path2 + '/' + i)
                self.walk(dir + '/' + i, path2 + '/' + i)
            else:
                if i.split('.')[-1].lower() not in ['ds_store', 'gz', 'db']:
                    n = dir + '/' + i
                    self.files_to_transfer.append([n, path2, i])

    def dir_files(self, path, path2):
        self.walk(path, path2)

    def compare_files(self, path, path2):

        os.chdir(path)
        self.ftp.cwd(path2)
        print path

        photos_list = ['jpg', 'png', 'mov', 'm4v', 'mp4']
        not_transfer = ['ds_store', 'gz', 'db']
        list_server = self.ftp.nlst()[2:]

        for file_ in os.listdir(os.getcwd()):
            if file_.split('.')[-1].lower() in not_transfer:
                continue
            else:
                if os.path.isfile(file_):
                    if file_ not in list_server:
                        self.files_to_transfer.append([path + '/' + file_, path2, file_])
                    else:
                        if file_.split('.')[-1].lower() in photos_list:
                            continue
                        else:
                            if self.get_ftp_md5(path2 + '/' + file_) != md5(path + '/' + file_):
                                self.files_to_transfer.append([path + '/' + file_, path2, file_]) # localizacion en local, nuevo directorio en servidor, nombre
                                list_server.pop(list_server.index(file_))
                elif os.path.isdir(file_):
                    if file_ not in self.ftp.nlst()[2:]:
                        self.ftp.mkd(path2 + '/' + file_)
                        self.dir_files(path + '/' + file_, path2 + '/' + file_)
                    else:
                        self.compare_files(path + '/' + file_, path2 + '/' + file_)

        os.chdir(('/'.join(path.split('/')[:-1])))
        self.ftp.cwd('/'.join(path2.split('/')[:-1]))


    def transfer_file(self, _file, dir_local, dir_out):
        print 'Transfering '+ _file + ' to ' + dir_out + '/' + _file
        self.ftp.cwd(dir_out)
        os.chdir(dir_local)
        myf = open(_file, 'rb')
        self.ftp.storbinary('STOR ' + _file, myf, 1024)
        myf.close()

    def serv_quit(self):
        self.ftp.quit()


if __name__ == "__main__":
    start = datetime.now()

    compare_path = '/public_html'
    my_path = '/local_path'
    serv = server('host', 'user', 'password')
    #serv.list_directory()
    print serv

    serv.compare_files(my_path, compare_path)

    end = datetime.now()
    print '\nTime taken. ', end - start

    if serv.files_to_transfer:
        print '\nThese files are not synchornized:\n'
        for n in serv.files_to_transfer:
            print n[0]
        if raw_input('\nDo you want to transfer them to your FTP server? (y/n) ').lower() == 'y':
            print ''
            for i in serv.files_to_transfer:
                serv.transfer_file(i[2], '/'.join(i[0].split('/')[:-1]), i[1])
            print ''
    else:
        print '\nThere are no files to update or transfer\n'

    serv.serv_quit()
