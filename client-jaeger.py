from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "secretkey123"

trace.set_tracer_provider(
TracerProvider(
        resource=Resource.create({SERVICE_NAME: "my-helloworld-service"})
    )
)
tracer = trace.get_tracer(__name__)


with tracer.start_as_current_span('first-trace'):
    carrier = {}
    # Write the current context into the carrier.
    TraceContextTextMapPropagator().inject(carrier)

carrier = {'traceparent': '00-a9c3b99a95cc045e573e163c3ac80a77-d99d251a8caecd06-01'}
ctx = TraceContextTextMapPropagator().extract(carrier=carrier)

# create a JaegerExporter
jaeger_exporter = JaegerExporter(
    # configure agent
    agent_host_name='192.168.59.3',
    agent_port=49153,
    # optional: configure also collector
    collector_endpoint='http://192.168.59.3:49153/api/traces?format=jaeger.thrift',
    # username=xxxx, # optional
    # password=xxxx, # optional
    # max_tag_value_length=None # optional
)

# Create a BatchSpanProcessor and add the exporter to it
span_processor = BatchSpanProcessor(jaeger_exporter)

# add to the tracer
trace.get_tracer_provider().add_span_processor(span_processor)


@app.route("/")  # this sets the route to this page
def home():
    with tracer.start_as_current_span('client-jaeger', context=ctx):
        response = requests.get("http://192.168.59.4/")
        return "client" + response.text
            



if __name__ == "__main__":
    app.run()

