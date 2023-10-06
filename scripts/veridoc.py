import matplotlib.pyplot as plt
import re
import argparse

# function that parses verilog and finds required declarations
def parse_verilog_file(verilog_file):
    try:
        with open(verilog_file, 'r') as file:
            verilog_code = file.read()

            # Find module name
            module_name = re.findall(r'module\s+([\w_]+)\s*\(', verilog_code)

            # Find parameters
            parameters = re.findall(r'\b(parameter|localparam)\s+(.+?);', verilog_code)

            # Find input ports
            input_ports = re.findall(r'\binput\b(.+?);', verilog_code)
            
            # Find output ports
            output_ports = re.findall(r'\boutput\b(.+?);', verilog_code)
    
    except FileNotFoundError:
        print(f"Error: File '{verilog_file}' not found.")
        exit()

    return module_name, parameters, input_ports, output_ports

# function to find the values of parameters and return a dictionary
def param_check(params):
    param_list = dict()
    for param in params:
        param_name = re.findall('(\w+)\s+=', param[1])
        param_value = re.findall("(\d+)", param[1])
        print(param, param_name, param_value)
        param_list[param_name[0]] = param_value[0]
        
    return param_list

# function to replace the parameter values in the port list       
def replace_params(param_dict, port_list):
    for i in range(len(port_list)):
        for key, value in param_dict.items():
            width_pattern = rf'\[{key}\s*-1:0\]'
            new_width = f'[{int(value)-1}:0]'
            port_list[i] = re.sub(width_pattern, new_width, port_list[i])
            
        port_list[i] = ' '.join(port_list[i].split()[::-1])
        print(port_list[i])
            
        port_list[i] = port_list[i].strip()
            
    return port_list

# function to split the interfaces into two equal halves    
def split_dict(dictionary):
    # Get a list of keys and their associated values
    items = list(dictionary.items())

    # Sort the list of items by the number of values 
    sorted_items = sorted(items, key=lambda x: len(x[1]))
    
    # Initialize two empty dictionaries to hold the two groups
    group1 = {}
    group2 = {}
    
    # Initialize variables to keep track of the sum of values in each group
    sum_group1 = 0
    sum_group2 = 0
    
    # Iterate through the sorted items and assign keys to the groups
    for key, value in sorted_items:
        # Assign to the group with the smaller sum
        if sum_group1 <= sum_group2:
            group1[key] = value
            sum_group1 += len(group1[key])
        else:
            group2[key] = value
            sum_group2 += len(group2[key])
    
    return group1, group2

# function that parses port list and associates the ports to respective interface groups
def interfaces(verilog_file, input_ports, output_ports):
    with open(verilog_file, 'r') as file:
        verilog_code = file.read()
        
    module_pattern = r'module\s+(\w+)\s*\((.*?)\);'
    module_match = re.search(module_pattern, verilog_code, re.DOTALL)
    if module_match:
        port_list = module_match.group(2)

        # Extract comments within port list
        comment_pattern = r'//(.*?)\n(.*?)(?=\n\s*//|$)'
        comment_matches = re.findall(comment_pattern, port_list, re.DOTALL)

        result = {}
        port_declarations = []
        for comment_match in comment_matches:
            comment = comment_match[0].strip()
            port_declarations = [port.replace(',','').strip() for port in comment_match[1].split(',\n')]
        
            for i, port_declaration in enumerate(port_declarations):
                for input_port in input_ports:
                    if re.search(port_declaration, input_port):
                        port_declarations[i] = input_port
                        # print (port_declarations[i])
                        break
                for output_port in output_ports:
                    if re.search(port_declaration, output_port):
                        port_declarations[i] = output_port
                        # print (port_declarations[i])
                        break
        # Store comment and port declarations in dictionary
            if comment not in result:
                result[comment] = []
            result[comment] = (port_declarations)
    
    # Split the dictionary into two groups
    left_dict, right_dict = split_dict(result) 
    print("\nLeft Interface:", end = " ")
    for key in left_dict:
        print("\n", key, end = "\t")
        for port in left_dict[key]:
            print(port, end = " ")
    print("\n\nRight Interface:", end = " ")
    for key in right_dict:
        print("\n", key, end = "\t") 
        for port in right_dict[key]:
            print(port, end = " ")

    return left_dict, right_dict


def dict_size(dictionary):
    size = 0
    for key in dictionary:
        size+= len(dictionary[key]) + 1
    return size

def draw_rectangle(ax, x, y, width, height, module_name):
    ax.add_patch(plt.Rectangle((x, y), width, height, facecolor='white', edgecolor='black', lw=1.5))
    
    module_text_x = x + width / 2
    module_text_y = y + height / 2
    ax.text(module_text_x, module_text_y, module_name, ha='center', va='center')

def write_interface(ax, x, y, interface_name, side):
    input_spacing = 0.5
    input_y = y * input_spacing
    if(side == 'left'):
        ax.text(x+1.5, input_y+0.1, interface_name, ha='right', va='center', weight='semibold')
    if(side == 'right'):    
        ax.text(x+0.5, input_y+0.1, interface_name, ha='left', va='center', weight='semibold')

def draw_input_ports(ax, x, y, input_port, side):
    input_spacing = 0.5
    input_y = y  * input_spacing
    if (side == 'left'):
        ax.arrow(x-0.1, input_y, 2, 0, head_width=0.08, head_length=0.1, fc='black', ec='black')
        ax.text(x+1.5, input_y + 0.2, input_port, ha='right', va='center')
    elif (side == 'right'):
        ax.arrow(x+2.1, input_y, -2, 0, head_width=0.08, head_length=0.1, fc='black', ec='black')
        ax.text(x+0.5, input_y + 0.2, input_port, ha='left', va='center')
        
def draw_output_ports(ax, x, y, output_port, side):
    output_spacing = 0.5
    output_y = y * output_spacing
    if (side == 'left'):
        ax.arrow(x+2, output_y, -2, 0, head_width=0.08, head_length=0.1, fc='black', ec='black')
        ax.text(x+1.5, output_y + 0.2, output_port, ha='right', va='center')
    if (side == 'right'):
        ax.arrow(x, output_y, 2, 0, head_width=0.08, head_length=0.1, fc='black', ec='black')
        ax.text(x+0.5, output_y + 0.2, output_port, ha='left', va='center')

def generate_module_diagram(module_name, left_dict, right_dict):
    fig, ax = plt.subplots(figsize=(10, 30))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 20)
    ax.set_aspect('equal')

    rect_x = 3
    rect_y = 0.5
    rect_width = 4
    rect_height = max(dict_size(left_dict), dict_size(right_dict)) * 0.5 + 0.5

    draw_rectangle(ax, rect_x, rect_y, rect_width, rect_height, module_name)
    
    left_intf_x = rect_x - 2
    left_intf_y = rect_y + (rect_height) + dict_size(left_dict)/2
    num_ports = 0
    for key in left_dict:
        write_interface(ax, left_intf_x, left_intf_y - num_ports, key, 'left')
        num_ports+=1
        for port in list(left_dict[key]):
            if(re.match('^i', port)):
                draw_input_ports(ax, left_intf_x, left_intf_y - num_ports, port, 'left')
            elif(re.match('^o',port)):
                draw_output_ports(ax, left_intf_x, left_intf_y - num_ports, port, 'left')
            num_ports+=1
    # Draw Right Interface 
    right_intf_x = rect_x + rect_width
    right_intf_y = rect_y + rect_height + dict_size(right_dict)/2
    num_ports = 0
    for key in right_dict:
        write_interface(ax, right_intf_x, right_intf_y - num_ports, key, 'right')
        num_ports+=1
        for port in list(right_dict[key]):
            if(re.match('^i', port)):
                draw_input_ports(ax, right_intf_x, right_intf_y - num_ports, port, 'right')
            elif(re.match('^o', port)):
                draw_output_ports(ax, right_intf_x, right_intf_y - num_ports, port, 'right')
            num_ports+=1


    # Disable x-y coords
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    # Save figure
    plt.savefig(module_name + '.jpg', dpi=1000, bbox_inches='tight')
    plt.close(fig)
    print("Finished\n")


def main():
    parser = argparse.ArgumentParser(description="Extract module name from Verilog file.")
    parser.add_argument("file_name", help="Path to the Verilog file")
    args = parser.parse_args()

    # Parse the file   
    verilog_file = args.file_name  
    module_name, parameters, input_ports, output_ports = parse_verilog_file(verilog_file)  
    if module_name:
        print("\nModule Name:", module_name[0])
    else:
        print("\nModule name not found.")
        
    # Replace parameters
    param_list = param_check(parameters)
    replace_params(param_list, output_ports)
    replace_params(param_list, input_ports)

    # Segregate two sides of the diagram 
    left_intf, right_intf = interfaces(verilog_file, input_ports, output_ports)

    # Generate diagram
    print("\n\nGenerating diagram...", end ="")
    generate_module_diagram(module_name[0], left_intf, right_intf)

if __name__ == '__main__':
    main()
