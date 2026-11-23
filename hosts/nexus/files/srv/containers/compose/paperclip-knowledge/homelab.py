#!/usr/bin/env python3
"""Small stdio MCP integrations using the installed official Python MCP SDK."""
import hashlib
import http.client
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
import asyncio
import inspect
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, ToolAnnotations, TextContent, ListToolsResult, CallToolResult

class SmallServer:
    """Use the installed SDK directly; no additional FastMCP dependency."""
    def __init__(self,name):
        self.functions={}
        async def listing(context,params):
            result=[]
            for name,function in self.functions.items():
                properties={};required=[]
                for key,param in inspect.signature(function).parameters.items():
                    schema={'type':{str:'string',int:'integer',float:'number'}[param.annotation]}
                    if param.default is inspect.Parameter.empty:required.append(key)
                    else:schema['default']=param.default
                    properties[key]=schema
                result.append(Tool(name=name,description=inspect.getdoc(function) or name,
                    inputSchema={'type':'object','properties':properties,'required':required,'additionalProperties':False},
                    annotations=ToolAnnotations(readOnlyHint=True,destructiveHint=False,idempotentHint=True)))
            return ListToolsResult(tools=result)
        async def call(context,params):
            name=params.name;arguments=params.arguments or {}
            if name not in self.functions:raise ValueError('Unknown tool')
            function=self.functions[name];inspect.signature(function).bind(**arguments)
            result=await asyncio.to_thread(function,**arguments)
            return CallToolResult(content=[TextContent(type='text',text=json.dumps(result))])
        self.server=Server(name,on_list_tools=listing,on_call_tool=call)
    def tool(self):
        def register(function):self.functions[function.__name__]=function;return function
        return register
    def run(self,transport='stdio'):
        async def serve():
            async with stdio_server() as (read,write):
                await self.server.run(read,write,self.server.create_initialization_options())
        asyncio.run(serve())

service = sys.argv[1]
mcp = SmallServer('Homelab ' + service)
def compact(value):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if any(s in k.lower() for s in ['password','passphrase','secret','token','credential','psk','privatekey','private_key','authkey','x_ssh','vwirekey','mgmt_key']) else compact(v) for k,v in value.items()}
    if isinstance(value, list): return [compact(v) for v in value[:300]]
    return value

if service == 'unifi':
    def request(path):
        connection = http.client.HTTPSConnection('192.168.1.1', context=ssl._create_unverified_context(), timeout=15)
        connection.connect()
        actual = hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()
        if actual != os.environ['UNIFI_TLS_SHA256']:
            connection.close()
            raise RuntimeError('UniFi TLS certificate pin changed; verify through trusted SSH')
        connection.request('GET', path, headers={'X-API-Key':os.environ['UNIFI_API_KEY'],'Accept':'application/json'})
        response=connection.getresponse(); body=response.read(); status=response.status; connection.close()
        if status != 200: raise RuntimeError(f'UniFi API returned HTTP {status}')
        return compact(json.loads(body))

    @mcp.tool()
    def unifi_overview() -> dict:
        """Read UniFi Network version and site inventory; no configuration changes."""
        return {'application':request('/proxy/network/integration/v1/info'), 'sites':request('/proxy/network/integration/v1/sites')}

    @mcp.tool()
    def unifi_inventory(kind: str, offset: int = 0, limit: int = 100) -> dict:
        """Read devices, clients, networks, wifi, firewall_zones or firewall_policies. Secrets are redacted."""
        paths={'devices':'devices','clients':'clients','networks':'networks','wifi':'wifi/broadcasts','firewall_zones':'firewall/zones','firewall_policies':'firewall/policies'}
        if kind not in paths: raise ValueError('Unsupported inventory kind')
        if offset < 0 or not 1 <= limit <= 200: raise ValueError('Use offset >= 0 and limit 1..200')
        site=os.environ['UNIFI_SITE_ID']
        return request(f'/proxy/network/integration/v1/sites/{site}/{paths[kind]}?offset={offset}&limit={limit}')

elif service == 'prometheus':
    def request(path, parameters=None):
        root=os.environ.get('PROMETHEUS_URL','http://192.168.5.2:30104').rstrip('/')
        url=root+'/api/v1/'+path
        if parameters: url+='?'+urllib.parse.urlencode(parameters)
        with urllib.request.urlopen(url, timeout=25) as response: data=json.load(response)
        if data.get('status') != 'success': raise RuntimeError('Prometheus rejected the request')
        return compact(data['data'])

    @mcp.tool()
    def prometheus_query(query: str) -> dict:
        """Evaluate read-only PromQL against the homelab datasource used by Grafana."""
        if not query or len(query)>4000: raise ValueError('Query must contain 1..4000 characters')
        return request('query', {'query':query,'timeout':'20s'})

    @mcp.tool()
    def prometheus_query_range(query: str, start: float, end: float, step: int = 60) -> dict:
        """Read historical PromQL using Unix timestamps; max 31 days and 5000 samples per series."""
        if not query or len(query)>4000 or end<=start or end-start>31*86400 or step<1 or (end-start)/step>5000:
            raise ValueError('Invalid range; increase step or reduce the time window')
        return request('query_range', {'query':query,'start':start,'end':end,'step':step,'timeout':'20s'})

    @mcp.tool()
    def prometheus_alerts() -> dict:
        """Read current Prometheus alert states without altering alert rules."""
        return request('alerts')

    @mcp.tool()
    def prometheus_targets() -> dict:
        """Read scrape target health, including unreachable host exporters."""
        data=request('targets',{'state':'active'})
        return {'targets':[{'labels':x.get('labels'), 'health':x.get('health'), 'last_scrape':x.get('lastScrape'), 'last_error':x.get('lastError')} for x in data.get('activeTargets',[])]}
else:
    raise SystemExit('Use unifi or prometheus')

if __name__ == '__main__': mcp.run(transport='stdio')
