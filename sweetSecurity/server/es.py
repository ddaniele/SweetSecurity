from urllib.parse import quote

JSON_HEADERS = {'Content-Type': 'application/json'}

def _doc_path(index, doc_type, doc_id=None, suffix=None):
	path = '/%s/%s' % (index, doc_type)
	if doc_id is not None:
		path += '/%s' % quote(str(doc_id), safe='')
	if suffix is not None:
		path += '/%s' % suffix
	return path

def write(es,body,index,doc_type):
	try:
		res = es.transport.perform_request(
			'POST',
			_doc_path(index, doc_type),
			body=body,
			headers=JSON_HEADERS
		)
		return res
	except Exception as e:
		return e

def search(es,body,index,doc_type,size=None,scrollId=None):
	if size is None:
		size=1000
	try:
		if scrollId is not None:
			res = es.transport.perform_request(
				'POST',
				'/_search/scroll',
				body={'scroll_id': scrollId},
				headers=JSON_HEADERS
			)
		else:
			res = es.transport.perform_request(
				'POST',
				_doc_path(index, doc_type, suffix='_search'),
				body=body,
				params={'size': size},
				headers=JSON_HEADERS
			)
		return res
	except Exception as e:
		print(str(e))
		return None


def update(es,body,index,doc_type,id):
	res = es.transport.perform_request(
		'POST',
		_doc_path(index, doc_type, id, '_update'),
		body=body,
		headers=JSON_HEADERS
	)
	return res

def delete(es,index,doc_type,id):
	res = es.transport.perform_request('DELETE', _doc_path(index, doc_type, id))
	return res

def compare(d1,d2):
	d1_keys = set(d1.keys())
	d2_keys = set(d2.keys())
	intersect_keys = d1_keys.intersection(d2_keys)
	compared = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
	return compared

def consolidate(mac,es):
	device1={}
	deviceQuery = {"query": {"match_phrase": {"mac": { "query": mac }}}}
	deviceInfo=search(es, deviceQuery, 'sweet_security', 'devices')
	for device in deviceInfo['hits']['hits']:
		if len(device1) > 0:
			modifiedInfo = compare(device1['_source'],device['_source'])
			#usually just two, but we'll keep the oldest one, since that one has probably been modified
			if modifiedInfo['firstSeen'][0] < modifiedInfo['firstSeen'][1]:
				deleteID=device['_id']
			else:
				deleteID=device1['_id']
			delete(es,'sweet_security','devices',deleteID)
		device1=device
