import os
import redis

def read_file_content(file_path):
    with open(file_path, "rb") as file:
        return file.read()

def store_files_in_redis(redis_host, redis_port, folder_path):
    # connect to redis server
    r = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
    # print(os.listdir(folder_path))
    # get files in folder
    files = [os.path.join(folder_path, f,fk) for f in os.listdir(folder_path) for fk in os.listdir(os.path.join(folder_path, f)) if os.path.isfile(os.path.join(folder_path, f,fk))]
    # print(files)
    for file_name in files:
        file_path = file_name
        # os.path.join(folder_path, file_name)
        redis_key = file_name.split("/")[-1]  # use file name as key
        print(file_path)
        file_content = read_file_content(file_path)

        # store file content in redis
        r.set(redis_key, file_content)
    
    print(r.keys())

if __name__ == "__main__":
    folder_path = "resources"

    # Redis configuration
    redis_host = "localhost"
    redis_port = 6379

    store_files_in_redis(redis_host, redis_port, folder_path)
