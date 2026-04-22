import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
from shapely.geometry import Polygon
from collections import Counter

# Generate voronoi
cells = 1000

points = np.random.rand(cells, 2)

vor = Voronoi(points)

# Boundary of foam
box = Polygon([(0,0), (1,0), (1,1), (0,1)])


# Handles case of infinite edges 
def voronoi_finite_polygons_2d(vor, radius=100):
    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)

    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    for p1, region_idx in enumerate(vor.point_region):
        region = vor.regions[region_idx]

        if all(v >= 0 for v in region):
            new_regions.append(region)
            continue

        new_region = [v for v in region if v >= 0]

        for p2, v1, v2 in all_ridges[p1]:
            if v1 >= 0 and v2 >= 0:
                continue

            v = v1 if v1 >= 0 else v2

            tangent = vor.points[p2] - vor.points[p1]
            tangent /= np.linalg.norm(tangent)

            normal = np.array([-tangent[1], tangent[0]])
            midpoint = vor.points[[p1, p2]].mean(axis=0)

            direction = np.sign(np.dot(midpoint - center, normal)) * normal
            far_point = vor.vertices[v] + direction * radius

            new_vertices.append(far_point.tolist())
            new_region.append(len(new_vertices) - 1)

        new_regions.append(new_region)

    return new_regions, np.array(new_vertices)

regions, vertices = voronoi_finite_polygons_2d(vor)

# Storage of voronoi info 
vertex_map = {}
vertices_list = []

def add_vertex(v):
    key = (round(v[0], 6), round(v[1], 6))
    if key not in vertex_map:
        vertex_map[key] = len(vertices_list)
        vertices_list.append(np.array(v))
    return vertex_map[key]

edges = []
edge_map = {}
faces = []

# Building and sorting edges for SE
for region in regions:
    poly_coords = vertices[region]

    # Sort vertices
    center = poly_coords.mean(axis=0)
    angles = np.arctan2(poly_coords[:,1] - center[1],
                        poly_coords[:,0] - center[0])
    poly_coords = poly_coords[np.argsort(angles)]

    poly = Polygon(poly_coords)

    # Fix invalid polygons before clipping (ie. duplicated verticies/edges)
    if not poly.is_valid:
        poly = poly.buffer(0)

    if poly.is_empty:
        continue

    # Makes it so that the polygons lie within the boundary 
    clipped = poly.intersection(box)

    # Handle invalid result after clipping
    if not clipped.is_valid:
        clipped = clipped.buffer(0)

    if clipped.is_empty:
        continue

    # Handle MultiPolygon (May happen after clipping where one cells gets split into multiple)
    # This keeps the larger of the split
    if clipped.geom_type == "MultiPolygon":
        clipped = max(clipped.geoms, key=lambda g: g.area)

    coords = list(clipped.exterior.coords[:-1])  # remove duplicate last point

    if len(coords) < 3:
        continue

    face_edges = []
    n = len(coords)

    for i in range(n):
        v1 = add_vertex(coords[i])
        v2 = add_vertex(coords[(i+1) % n])

        key = (v1, v2)
        rev = (v2, v1)

        if key in edge_map:
            eid = edge_map[key]
            face_edges.append(eid)
        elif rev in edge_map:
            eid = edge_map[rev]
            face_edges.append(-eid)
        else:
            eid = len(edges) + 1
            edge_map[key] = eid
            edges.append((v1, v2))
            face_edges.append(eid)

    faces.append(face_edges)

vertices_array = np.array(vertices_list)

# Write fe file
def write_fe(filename, vertices, edges, faces):
    edge_count = Counter()
    for fedges in faces:
        for e in fedges:
            edge_count[abs(e)] += 1  

    boundary_edges = {e for e, count in edge_count.items() if count == 1}

    boundary_vertices = set()
    for i, (v1, v2) in enumerate(edges, start=1):
        if i in boundary_edges:
            boundary_vertices.add(v1)
            boundary_vertices.add(v2)

    with open(filename, "w") as f:
        f.write("STRING\n")
        f.write("space_dimension 2\n")

        f.write("\nvertices\n")
        for i, (x, y) in enumerate(vertices, start=1):
            if (i - 1) in boundary_vertices:
                f.write(f"{i} {x:.6f} {y:.6f} FIXED\n")
            else:
                f.write(f"{i} {x:.6f} {y:.6f}\n")

        f.write("\nedges\n")
        for i, (v1, v2) in enumerate(edges, start=1):
            if i in boundary_edges:
                f.write(f"{i} {v1+1} {v2+1} FIXED\n")
            else:
                f.write(f"{i} {v1+1} {v2+1}\n")

        f.write("\nfaces\n")
        for i, fedges in enumerate(faces, start=1):
            f.write(f"{i} {' '.join(map(str, fedges))}\n")

write_fe("foam.fe", vertices_array, edges, faces)

# Plot Voronoi
fig, ax = plt.subplots(figsize=(6,6))

for v1, v2 in edges:
    p1 = vertices_array[v1]
    p2 = vertices_array[v2]
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'k-')

square = plt.Rectangle((0,0), 1,1, fill=False, color='black', lw=2)
ax.add_patch(square)

ax.set_aspect('equal')
ax.set_xlim(0,1)
ax.set_ylim(0,1)
ax.axis('off')

plt.show()


#Edge Frequency Distribution
edge_counts = [len(face) for face in faces]

weights = np.ones(len(edge_counts)) / len(faces) * 100  # convert to percent

plt.hist(edge_counts,
         bins=range(min(edge_counts), max(edge_counts)+2),
         weights=weights,
         align='left',
         edgecolor='black')

plt.xlabel("Number of Edges")
plt.ylabel("Percentage of Cells (%)")
plt.title("Distribution of Edge Counts")
plt.show()

#Area of cells using Shoelace Formula 
def polygon_area(coords):
    """Shoelace formula for area of a polygon"""
    x = coords[:, 0]
    y = coords[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def get_face_vertices(face_edges, edges, vertices):
    """Reconstruct ordered vertex list for a face"""
    coords = []

    for i, e in enumerate(face_edges):
        v1, v2 = edges[abs(e) - 1]

        if e > 0:
            start, end = v1, v2
        else:
            start, end = v2, v1

        if i == 0:
            coords.append(vertices[start])
            coords.append(vertices[end])
        else:
            coords.append(vertices[end])

    return np.array(coords)

# Compute areas
areas = []

for face in faces:
    coords = get_face_vertices(face, edges, vertices_array)
    
    # Remove duplicate last point if present
    if np.allclose(coords[0], coords[-1]):
        coords = coords[:-1]

    area = polygon_area(coords)
    areas.append(area)

areas = np.array(areas)

print("Min area:", areas.min())
print("Max area:", areas.max())
print("Mean area:", areas.mean())
print("Total area:", areas.sum())


# Plot distributions as percentage of cells 
weights = np.ones(len(areas)) / len(areas) * 100  # each cell contributes %

plt.hist(areas,
         bins=25,
         weights=weights,
         edgecolor='black')

plt.xlabel("Cell Area")
plt.ylabel("Percentage of Cells (%)")
plt.title("Distribution of Cell Areas")
plt.show()
