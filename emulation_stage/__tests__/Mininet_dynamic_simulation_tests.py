def compute_link_delta(old_link, new_link):
    old_intermediate = old_link[1:-1]
    new_intermediate = new_link[1:-1]
    handover_arr = [0] * (len(new_intermediate) - 1)
    # j is the old link pointer
    j = 0
    for i in range(0, len(new_intermediate)):
        if new_intermediate[i] in old_intermediate:
            # ends the difference
            if old_intermediate.index(new_intermediate[i]) != j:
                handover_arr[i - 1] = 1
                j = old_intermediate.index(new_intermediate[i])
            j += 1
        else:
            # starts the difference
            if i > 0 and new_intermediate[i - 1] in old_intermediate:
                handover_arr[i - 1] = 1
    
    return [0] + handover_arr + [0]


print(compute_link_delta([-1, 749, 8, 812, 11, 876, 14, 67, 79, 45, 1395, -2], [-1, 749, 8, 812, 14, 68, 79, 45, 1395, -2]))

print(compute_link_delta([-1, 749, 8, 812, 11, 876, 14, 68, 79, 45, 1395, -2], [-1, 749, 8, 812, 14, 68, 79, 45, 1395, -2]))

print(compute_link_delta([-1, 749, 8, 812, 14, 68, 79, 45, 1010, -2], [-1, 749, 3, 1197, 11, 876, 14, 68, 79, 45, 1010, -2]))

print(compute_link_delta([-1, 749, -2], [-1, 750, -2]))

print(compute_link_delta(["NULL"], [-1, 749, 3, 1197, 11, 876, 14, 68, 79, 45, 1010, -2]))



