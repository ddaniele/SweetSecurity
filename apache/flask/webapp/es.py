from urllib.parse import quote, urlencode

def _doc_path(index, doc_type, doc_id=None, suffix=None):
	path = '/%s/%s' % (index, doc_type)
	if doc_id is not None:
		path += '/%s' % quote(str(doc_id), safe='')
	if suffix is not None:
		path += '/%s' % suffix
	return path

def _perform_request(es, method, path, body=None, params=None):
	try:
		if params is not None:
			return es.transport.perform_request(method, path, body=body, params=params)
		return es.transport.perform_request(method, path, body=body)
	except TypeError:
		if params:
			path = '%s?%s' % (path, urlencode(params))
		return es.transport.perform_request(method, path, body=body)

def write(es,body,index,doc_type):
	try:
		res = _perform_request(es, 'POST', _doc_path(index, doc_type), body=body)
		return res
	except Exception as e:
		return e

def search(es,body,index,doc_type,size=None):
	if size is None:
		size=1000
	try:
		res = _perform_request(
			es,
			'POST',
			_doc_path(index, doc_type, suffix='_search'),
			body=body,
			params={'size': size}
		)
		return res
	except Exception as e:
		print(str(e))
		return None

def update(es,body,index,doc_type,id):
	res = _perform_request(es, 'POST', _doc_path(index, doc_type, id, '_update'), body=body)
	return res

def delete(es,index,doc_type,id):
	res = _perform_request(es, 'DELETE', _doc_path(index, doc_type, id))
	return res

def compare(d1,d2):
	d1_keys = set(d1.keys())
	d2_keys = set(d2.keys())
	intersect_keys = d1_keys.intersection(d2_keys)
	compared = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
	return compared

def consolidate(mac,es,type):
	device1={}
	deviceQuery = {"query": {"match_phrase": {"mac": { "query": mac }}}}
	deviceInfo=search(es, deviceQuery, 'sweet_security', type)
	for device in deviceInfo['hits']['hits']:
		if len(device1) > 0:
			modifiedInfo = compare(device1['_source'],device['_source'])
			#usually just two, but we'll keep the oldest one, since that one has probably been modified
			if modifiedInfo['firstSeen'][0] < modifiedInfo['firstSeen'][1]:
				deleteID=device['_id']
			else:
				deleteID=device1['_id']
			delete(es,'sweet_security',type,deleteID)
		device1=device

