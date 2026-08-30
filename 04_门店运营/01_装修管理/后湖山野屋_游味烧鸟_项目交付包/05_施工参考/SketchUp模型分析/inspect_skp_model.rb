# encoding: UTF-8
require 'json'
require 'fileutils'

module CodexSkpInspect
  MODEL_PATH = 'D:/桌面/改造方案.skp'.freeze
  OUT_DIR = 'C:/Users/admin/AppData/Local/Temp/codex_skp_analysis'.freeze

  def self.cm(value)
    (value.to_f * 2.54).round(2)
  end

  def self.point_cm(point)
    [cm(point.x), cm(point.y), cm(point.z)]
  end

  def self.bounds_hash(bounds, transform = IDENTITY)
    points = (0..7).map { |i| bounds.corner(i).transform(transform) }
    xs = points.map(&:x); ys = points.map(&:y); zs = points.map(&:z)
    {
      'min_cm' => [cm(xs.min), cm(ys.min), cm(zs.min)],
      'max_cm' => [cm(xs.max), cm(ys.max), cm(zs.max)],
      'size_cm' => [cm(xs.max - xs.min), cm(ys.max - ys.min), cm(zs.max - zs.min)],
      'center_cm' => [cm((xs.max + xs.min) / 2.0), cm((ys.max + ys.min) / 2.0), cm((zs.max + zs.min) / 2.0)]
    }
  end

  def self.entity_label(entity)
    name = entity.respond_to?(:name) ? entity.name.to_s.strip : ''
    if name.empty? && entity.respond_to?(:definition)
      name = entity.definition.name.to_s.strip
    end
    name.empty? ? "#{entity.typename}_#{entity.entityID}" : name
  end

  def self.walk_entities(entities, parent_transform, path, rows, stats, depth = 0)
    entities.each do |entity|
      stats[entity.typename] = stats.fetch(entity.typename, 0) + 1
      next unless entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)

      transform = parent_transform * entity.transformation
      label = entity_label(entity)
      definition = entity.definition
      row = {
        'path' => (path + [label]).join(' / '),
        'type' => entity.typename,
        'name' => label,
        'definition' => definition.name.to_s,
        'tag' => entity.layer ? entity.layer.name.to_s : '',
        'visible' => entity.visible?,
        'locked' => entity.locked?,
        'depth' => depth,
        'bounds' => bounds_hash(definition.bounds, transform),
        'origin_cm' => point_cm(ORIGIN.transform(transform))
      }
      rows << row
      walk_entities(definition.entities, transform, path + [label], rows, stats, depth + 1)
    end
  end

  def self.camera_hash(camera)
    {
      'eye_cm' => point_cm(camera.eye),
      'target_cm' => point_cm(camera.target),
      'up' => [camera.up.x.round(5), camera.up.y.round(5), camera.up.z.round(5)],
      'perspective' => camera.perspective?,
      'fov_degrees' => camera.fov.round(3)
    }
  end

  def self.write_view(view, name, eye, target, up, perspective = false)
    view.camera = Sketchup::Camera.new(eye, target, up, perspective)
    view.zoom_extents
    view.refresh
    view.write_image(
      :filename => File.join(OUT_DIR, "#{name}.png"),
      :width => 1800,
      :height => 1100,
      :antialias => true,
      :compression => 0.9,
      :transparent => false
    )
  end

  def self.run
    FileUtils.mkdir_p(OUT_DIR)
    log_path = File.join(OUT_DIR, 'analysis_log.txt')
    File.write(log_path, "SketchUp inspection started\n")

    unless File.exist?(MODEL_PATH)
      raise "Model not found: #{MODEL_PATH}"
    end

    model = Sketchup.active_model
    if model.path.to_s.tr('\\', '/') != MODEL_PATH
      status = Sketchup.open_file(MODEL_PATH)
      File.open(log_path, 'a') { |f| f.puts("open_file status=#{status}") }
      model = Sketchup.active_model
    end

    units = model.options['UnitsOptions']
    rows = []
    stats = {}
    walk_entities(model.entities, IDENTITY, [], rows, stats)
    bounds = model.bounds
    center = bounds.center
    max_dim = [bounds.width, bounds.height, bounds.depth].max
    distance = [max_dim * 2.8, 1000.0].max

    pages = model.pages.map do |page|
      {
        'name' => page.name.to_s,
        'camera' => camera_hash(page.camera),
        'use_camera' => page.use_camera?
      }
    end

    data = {
      'source_file' => MODEL_PATH,
      'sketchup_version' => Sketchup.version,
      'model_title' => model.title.to_s,
      'model_description' => model.description.to_s,
      'units_raw' => {
        'LengthUnit' => units['LengthUnit'],
        'LengthFormat' => units['LengthFormat'],
        'LengthPrecision' => units['LengthPrecision'],
        'SuppressUnitsDisplay' => units['SuppressUnitsDisplay']
      },
      'model_bounds' => bounds_hash(bounds),
      'entity_counts_recursive' => stats,
      'groups_and_components_count' => rows.length,
      'groups_and_components' => rows.sort_by { |r| [-r['bounds']['size_cm'][0] * r['bounds']['size_cm'][1] * r['bounds']['size_cm'][2], r['path']] },
      'tags' => model.layers.map { |layer| {'name' => layer.name.to_s, 'visible' => layer.visible?} },
      'scenes' => pages,
      'active_camera' => camera_hash(model.active_view.camera)
    }
    File.write(File.join(OUT_DIR, 'model_analysis_cm.json'), JSON.pretty_generate(data))

    view = model.active_view
    original_camera = view.camera
    z_up = Geom::Vector3d.new(0, 0, 1)
    y_up = Geom::Vector3d.new(0, 1, 0)
    write_view(view, '01_top', center.offset(z_up, distance), center, y_up, false)
    write_view(view, '02_front', Geom::Point3d.new(center.x, center.y - distance, center.z), center, z_up, false)
    write_view(view, '03_back', Geom::Point3d.new(center.x, center.y + distance, center.z), center, z_up, false)
    write_view(view, '04_left', Geom::Point3d.new(center.x - distance, center.y, center.z), center, z_up, false)
    write_view(view, '05_right', Geom::Point3d.new(center.x + distance, center.y, center.z), center, z_up, false)
    write_view(view, '06_iso', Geom::Point3d.new(center.x - distance, center.y - distance, center.z + distance * 0.75), center, z_up, true)
    view.camera = original_camera

    export_options = {
      :units => 'cm',
      :triangulated_faces => false,
      :doublesided_faces => true,
      :edges => true,
      :texture_maps => true,
      :selectionset_only => false,
      :show_summary => false
    }
    export_status = model.export(File.join(OUT_DIR, '改造方案_厘米单位.obj'), export_options)
    File.open(log_path, 'a') { |f| f.puts("obj_export status=#{export_status}") }
    File.write(File.join(OUT_DIR, 'DONE.flag'), Time.now.to_s)
  rescue => error
    FileUtils.mkdir_p(OUT_DIR)
    File.write(File.join(OUT_DIR, 'ERROR.txt'), "#{error.class}: #{error.message}\n#{error.backtrace.join("\n")}")
  end
end

UI.start_timer(3.0, false) { CodexSkpInspect.run }
