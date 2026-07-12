    def _uploadAttachment(self, filePath, thread_id, thread_type):
        if not os.path.exists(filePath):
            raise ZaloUserError(f"{filePath} not found")
        
        ext = os.path.splitext(filePath)[1][1:].lower()
        urlType = {
            "image": "photo_original/upload",
            "aac": "voice/upload",
            "video": "asyncfile/upload",
            "gif": "gif?",
            "others": "asyncfile/upload"
        }
        max_size = 9 * 1000 * 1000
        file_size = os.path.getsize(filePath)
        maxtype = ""

        if ext in ["jpg", "jpeg", "png"]:
            fileType = "image"
        elif ext in ["mp3", "aac"]:
            if file_size > max_size:
                fileType = "others"
                maxtype = "voice.aac"
            else:
                fileType = "aac"
        elif ext == "mp4":
            fileType = "video"
        else:
            fileType = "others"

        if thread_type == ThreadType.USER:
            base_url = "https://tt-files-wpa.chat.zalo.me/api/message/"
            params = {"type": 2}
            params_extra = {"toid": str(thread_id)}
        else:
            base_url = "https://tt-files-wpa.chat.zalo.me/api/group/"
            params = {"type": 11}
            params_extra = {"grid": str(thread_id)}

        params.update({
            "zpw_ver": 649,
            "zpw_type": 30
        })

        chunk_size = 3145728
        total_chunks = math.ceil(file_size / chunk_size)
        clientId = int(time.time() * 1000)

        def upload_single_chunk(chunk_id, chunk):
            max_retries = 5
            retry_count = 0
            while retry_count < max_retries:
                try:
                    chunk_params = {
                        "totalChunk": total_chunks,
                        "fileName": os.path.basename(filePath),
                        "fileType": fileType,
                        "clientId": clientId,
                        "totalSize": file_size,
                        "imei": self._imei,
                        "isE2EE": 0,
                        "jxl": 0,
                        "chunkId": chunk_id,
                        **params_extra
                    }
                    params["params"] = self._encode(chunk_params)
                    files = [("chunkContent", (os.path.basename(filePath), chunk, "application/octet-stream"))]
                    url = base_url + urlType[fileType]
                    response = self._post(url, params=params.copy(), files=files,timeout=5)
                    data = response.json()
                    break
                except Exception as e:
                    print(f"\nLỗi khi upload chunk {chunk_id}: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"\rĐang thử lại chunk {chunk_id}/{total_chunks} lần {retry_count}...", end="")
                    if retry_count > max_retries:
                        print(f"\rHết lượt thử lại", end="")

            # percent = (chunk_id / total_chunks) * 100
            # print(f"\rĐang upload {os.path.basename(filePath)}: {percent:.2f}%", end="")

            if data.get("error_code") == 0:
                results = self._decode(data["data"])
                if results.get("error_code") == 0:
                    results = results.get("data")
                    if results.get("fileId") and results["fileId"] != "-1":
                        future = Future()

                        def callback(ws_data):
                            future.set_result({
                                "fileName": os.path.basename(filePath),
                                "totalSize": os.path.getsize(filePath),
                                "fileType": fileType,
                                "fileUrl": ws_data['fileUrl'],
                                "fileId": ws_data['fileId']
                            })

                        self.uploadCallbacks[str(results["fileId"])] = callback
                        res = future.result()
                        if maxtype:
                            url = res["fileUrl"]
                            res["fileUrl"] = f"{url}/{maxtype}"
                        print(f"\nĐã upload thành công file {res['fileName']}")
                        return res
                    elif results.get("photoId") and results.get("finished"):
                        return {
                            "fileType": fileType,
                            **results
                        }

            return None

        with open(filePath, 'rb') as f, ThreadPoolExecutor(max_workers=10) as executor:
            chunk_id = 1
            while chunk_id <= total_chunks:
                futures = []
                percent = (chunk_id / total_chunks) * 100
                print(f"\rĐang upload {os.path.basename(filePath)}: {percent:.2f}%", end="")
                for _ in range(2):
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    futures.append(executor.submit(upload_single_chunk, chunk_id, chunk))
                    chunk_id += 1

                for future in futures:
                    result = future.result()
                    if result:
                        return result

        raise ZaloAPIException("Upload failed: No successful chunk returned.")