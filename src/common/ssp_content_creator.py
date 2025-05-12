from loguru import logger
from saxonche import *
# import os

TAB = "   "


def indent(level=0):
    return (TAB * level)

def transform_xml(in_file, xslt_file):
    status = False
    return_content = ""
    xslt_file = normalize_content(xslt_file)
    ok_to_continue = False

    print("XML to JSON 1 of 3")
    proc = PySaxonProcessor(license=False)
    # with PySaxonProcessor(license=False) as proc:

    xsltproc = proc.new_xslt30_processor()
    executable = xsltproc.compile_stylesheet(stylesheet_text=xslt_file) 

    print("XML to JSON 2 of 3")
    document = proc.parse_xml(xml_text=in_file)

    print("XML to JSON 3 of 3")
    # return_content = executable.apply_templates_returning_string(source=document)
    return_content = executable.transform_to_string(xdm_node=document)

    return return_content



def LFS_get_file(file_name):
    ret_value = ""

    try:
        file = open(file_name, "rb")
        ret_value = file.read()
        file.close()
    except OSError:
        print("Could not open/read " + file_name)

    return ret_value

def normalize_content(content):
    ret_value = ""

    if isinstance(content, str):
        # ret_value = content.encode("utf-8") # convert to bytes
        # print ("Encode")
        print("Already string - do nothing")
    elif isinstance(content, bytes):
        ret_value = content.decode("utf-8")
        print("Decode")
    else:
        print("Unhandled content encoding: " + type(content))

    return ret_value





class oscal:
    def __init__(self, content):
        self.content = content
        self.valid = False
        self.root_node = ""
        self.oscal_format = ""
        self.oscal_version = ""
        self.oscal_model = ""

        self.proc = PySaxonProcessor(license=False)
        try: 
            self.xdm = self.proc.parse_xml(xml_text=content)
            # self.proc.declare_namespace("", "http://csrc.nist.gov/ns/oscal/1.0")
            self.valid = True
            self.oscal_format = "xml"
        except:
            logger.error("Content does not appear to be valid XML. Unable to rpoceed")

        if self.valid:
            self.xp = self.proc.new_xpath_processor() # Instantiates XPath processing
            self.list_ns()
            self.xp.set_context(xdm_item=self.xdm) # Sets xpath processing context as the whole file
            temp_ret = self.xpath_global("/*/name()")
            if temp_ret is not None:
                self.root_node = temp_ret[0].get_atomic_value().string_value
                logger.debug("ROOT: " + self.root_node)
            self.oscal_version = self.xpath_global_single("/*/*:metadata/*:oscal-version/text()")
            logger.debug("OSCAL VERSION: " + self.oscal_version)


    def list_ns(self):
        node_ = self.xdm
        child = node_.children[0]
        assert child is not None
        namespaces = child.axis_nodes(8)

        assert len(namespaces) > 0

        for ns in namespaces:
            uri_str = ns.string_value
            ns_prefix = ns.name

            if ns_prefix is not None:
                logger.debug("xmlns:" + ns_prefix + "='" + uri_str + "'")
            else:
                logger.debug("xmlns uri=" + uri_str + "'")
                # set default ns here
                self.xp.declare_namespace("", uri_str)


    def xpath_global(self, expression):
        ret_value = None
        logger.debug("Global Evaluating: " + expression)
        ret = self.xp.evaluate(expression)
        if  isinstance(ret,PyXdmValue):
            logger.debug("--Return Size: " + str(ret.size))
            ret_value = ret
        else:
            logger.debug("--No result")

        return ret_value

    def xpath_global_single(self, expression):
        ret_value = ""
        logger.debug("Global Evaluating Single: " + expression)
        ret = self.xp.evaluate_single(expression)
        if  isinstance(ret, PyXdmValue): # isinstance(ret,PyXdmNode):
            ret_value = ret.string_value
        else:
            logger.debug("--No result")
            logger.debug("TYPE: " + str(type(ret)))

        return ret_value


    def xpath(self, context, expression):
        ret_value = None
        logger.debug("Evaluating: " + expression)
        xp = self.proc.new_xpath_processor() # Instantiates XPath processing
        xp.set_context(xdm_item=context)
        ret = xp.evaluate(expression)
        if  isinstance(ret,PyXdmValue):
            logger.debug("--Return Size: " + str(ret.size))
            ret_value = ret
        else:
            logger.debug("--No result")

        return ret_value

    def xpath_single(self, context, expression):
        ret_value = ""
        logger.debug("Evaluating Single: " + expression)
        xp = self.proc.new_xpath_processor() # Instantiates XPath processing
        xp.set_context(xdm_item=context)
        ret = xp.evaluate_single(expression)
        if  isinstance(ret, PyXdmValue): # isinstance(ret,PyXdmNode):
            ret_value = ret.string_value
        else:
            logger.debug("--No result")
            logger.debug("TYPE: " + str(type(ret)))

        return ret_value



def putfile(file_name, content):
    logger.debug("LFS Put File " + file_name)
    status = False
    try:
        with open(file_name, mode='w') as file:
            file.write(content)
            file.close()
        status = True
    except (Exception, BaseException) as error:
        logger.error("Error saving file to local FS " + file_name + "(" + type(error).__name__ + ") " + str(error))

    return status

def process_params(catalog_obj, xpath_expression):
    param_output = ""
    logger.debug("Expr: " + xpath_expression)
    params = catalog_obj.xpath_global(xpath_expression)
    if params is not None:
        logger.debug("PARAMS FOUND: " + str(params.size))
        for param in params:
            param_id = (catalog_obj.xpath_single(param, "./@id")).strip()
            param_output += indent(3) + "<set-parameter param-id='" + param_id + "'>\n"
            param_output += indent(4) + "<value>placeholder</value>\n"
            param_output += indent(3) + "</set-parameter>\n"
    else:
        logger.debug("NO PARAMS FOUND")
    return param_output

def process_response_points(catalog_obj, xpath_expression, statement_uuid):
    rp_output = ""
    uuid_statement_incr = 100

    logger.debug("Expr: " + xpath_expression)
    logger.debug("---")
    response_points = catalog_obj.xpath_global(xpath_expression)
    if response_points is not None:
        logger.debug("RPs FOUND: " + str(response_points.size))
        for rp in response_points:
            statement_uuid += uuid_statement_incr
            rp_id = (rp.string_value).strip()
            rp_output += indent(3) + "<statement statement-id='" + rp_id + "' uuid='" + uuid_format(statement_uuid) + "'>\n"
            rp_output += process_components(statement_uuid)
            # rp_output += indent(4) + "<value>placeholder</value>\n"
            rp_output += indent(3) + "</statement>\n"
    else:
        logger.debug("NO STATEMENTS FOUND")
    return rp_output

def process_components(by_component_uuid): # catalog_obj, xpath_expression, control_uuid):
    comp_out = ""
    uuid_component_incr = 1

    by_component_uuid += uuid_component_incr
    comp_out += indent(4) + "<by-component component-uuid='11111111-2222-4000-8000-009000000000' uuid='" + uuid_format(by_component_uuid) + "'>\n"
    comp_out += indent(5) + "<description><p>This is the 'this-system' component.</p></description>\n"
    comp_out += indent(5) + "<implementation-status state='operational' />\n"
    comp_out += indent(4) + "</by-component>\n"

    return comp_out

def uuid_format(uuid_suffix):
    uuid_prefix = "11111111-2222-4000-8000-"
    return uuid_prefix + "{:012d}".format(uuid_suffix)

def process_catalog(catalog_obj):
    viable = False
    print("Processing ...")
    ssp_control_output = ""
    uuid_cntr=12000000000
    uuid_control_incr = 10000

    # xpath = "//*:group/*:control"
    xpath_expression = "//control"
    # rp_expansion = "/ ( *:part[@name='statement' and ./*:prop[@name='response-point' and @ns='https://fedramp.gov/ns/oscal']] |  *:part[@name='statement']//*:part[@name ='item' and ./*:prop[@name='response-point' and @ns='https://fedramp.gov/ns/oscal']] )  /@id"
    rp_expansion = "/part[@name='statement']//prop[@name='response-point' and @ns='https://fedramp.gov/ns/oscal']/../@id"
    controls = catalog_obj.xpath_global(xpath_expression)
    if  isinstance(controls,PyXdmValue):
        print(controls.size)
        for control_obj in controls:
            uuid_cntr += uuid_control_incr
            control_id = (catalog_obj.xpath_single(control_obj, "./@id")).strip()
            # if isinstance(detail_ret, PyXdmAtomicValue) or isinstance(detail_ret, PyXdmNode):
            print("CONTROL: " + control_id)
            ssp_control_output += indent(2) + "<implemented-requirement control-id='" + control_id + "' uuid='" + uuid_format(uuid_cntr) + "'>\n"
            ssp_control_output += process_params(catalog_obj, xpath_expression + "[@id='" + control_id + "']/param")
            ssp_control_output += process_response_points(catalog_obj, xpath_expression + "[@id='" + control_id + "']" + rp_expansion, uuid_cntr)
            
            ssp_control_output += indent(2) + "</implemented-requirement>\n"

    else:
        print("TYPE: " + str(type(controls)))

    return ssp_control_output



catalog = "../data/FedRAMP_rev5_HIGH-baseline-resolved-profile_catalog.xml"
ssp_controls = "../data/ssp_controls_fragment.xml"
ssp_control_output = ""

test_file = normalize_content(LFS_get_file(catalog))
catalog_obj = oscal(test_file)

if catalog_obj is not None:
    ssp_control_output = process_catalog(catalog_obj)

putfile(ssp_controls, ssp_control_output)


